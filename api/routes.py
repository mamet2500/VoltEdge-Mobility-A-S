import logging
import os
from functools import wraps
from flask import Blueprint, jsonify, request
from domain.value_objects.telemetry_reading import TelemetryReading
from domain.events.domain_events import TelemetryReceived, IncidentCreated, IncidentResolved
from domain.services.fault_detection import FaultDetectionService
from domain.services.predictive_maintenance import PredictiveMaintenanceService
from infrastructure.mysqlrepo import MySQLRepository

logger = logging.getLogger(__name__)
api = Blueprint("api", __name__)

repo = MySQLRepository(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    database=os.environ.get("DB_NAME", "voltedge_monitoring"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", "")
)

fault_service = FaultDetectionService()
predictive_service = PredictiveMaintenanceService()
API_KEY = os.environ.get("API_KEY", "voltedge-dev-key")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            logger.warning("Uautoriseret adgang fra %s", request.remote_addr)
            return jsonify({"error": "Ugyldig eller manglende API key"}), 401
        return f(*args, **kwargs)
    return decorated

def error_response(message, status_code):
    return jsonify({"error": message}), status_code

@api.route("/health", methods=["GET"])
def health():
    """
    Liveness check
    ---
    tags:
      - Health
    responses:
      200:
        description: Service koerer
    """
    return jsonify({"status": "ok", "service": "voltedge-monitoring"})

@api.route("/chargers", methods=["GET"])
@require_api_key
def get_chargers():
    """
    Hent alle ladestandere
    ---
    tags:
      - Chargers
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
    responses:
      200:
        description: Liste af ladestandere
      401:
        description: Ugyldig API key
    """
    chargers = repo.get_chargers()
    logger.info("GET /chargers – %d ladestandere", len(chargers))
    return jsonify(chargers)

@api.route("/chargers/<int:charger_id>", methods=["GET"])
@require_api_key
def get_charger(charger_id):
    """
    Hent en ladestander med connectors
    ---
    tags:
      - Chargers
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
      - name: charger_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Ladestander
      404:
        description: Ikke fundet
    """
    charger = repo.get_charger_by_id(charger_id)
    if not charger:
        return error_response("Ladestander ikke fundet", 404)
    charger["connectors"] = repo.get_connectors_by_charger(charger_id)
    return jsonify(charger)

@api.route("/telemetry", methods=["POST"])
@require_api_key
def create_telemetry():
    """
    Modtag telemetridata fra ladestander
    ---
    tags:
      - Telemetry
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - connector_id
            - voltage
            - current_amp
            - power_kw
            - status
          properties:
            connector_id:
              type: integer
              example: 1
            voltage:
              type: number
              example: 230.0
            current_amp:
              type: number
              example: 16.0
            power_kw:
              type: number
              example: 11.0
            temperature:
              type: number
              example: 42.5
            status:
              type: string
              example: available
            error_code:
              type: string
              example: null
    responses:
      201:
        description: Telemetri modtaget
      400:
        description: Ugyldigt payload
      404:
        description: Connector ikke fundet
    """
    payload = request.get_json(silent=True)
    required = ["connector_id", "voltage", "current_amp", "power_kw", "status"]
    if payload is None or any(k not in payload for k in required):
        return error_response(f"Paakraevede felter: {required}", 400)

    connector_id = int(payload["connector_id"])
    connector = repo.get_connector_by_id(connector_id)
    if not connector:
        return error_response(f"Connector {connector_id} ikke fundet", 404)

    charger = repo.get_charger_by_id(connector["charger_id"])

    try:
        reading = TelemetryReading(
            connector_id=connector_id,
            voltage=float(payload["voltage"]),
            current_amp=float(payload["current_amp"]),
            power_kw=float(payload["power_kw"]),
            temperature=float(payload["temperature"]) if payload.get("temperature") else None,
            status=payload["status"],
            error_code=payload.get("error_code")
        )
    except ValueError as e:
        return error_response(str(e), 400)

    repo.create_telemetry_reading(
        connector_id=reading.connector_id,
        voltage=reading.voltage,
        current_amp=reading.current_amp,
        power_kw=reading.power_kw,
        temperature=reading.temperature,
        status=reading.status,
        error_code=reading.error_code
    )
    repo.update_connector_status(connector_id, reading.status)
    repo.update_charger_status(connector["charger_id"], reading.status)

    event = TelemetryReceived(
        connector_id=connector_id,
        charger_serial=charger["serial_number"],
        voltage=reading.voltage,
        current_amp=reading.current_amp,
        power_kw=reading.power_kw,
        status=reading.status,
        error_code=reading.error_code
    )
    logger.info("TelemetryReceived: connector=%s charger=%s status=%s",
                event.connector_id, event.charger_serial, event.status)

    fault_event = fault_service.evaluate(reading, charger["serial_number"])

    if fault_event is None:
        return jsonify({"message": "Telemetri modtaget – ingen fejl", "connector_id": connector_id,
                        "status": reading.status, "fault_detected": False}), 201

    incident_id = repo.create_incident(
        connector_id=fault_event.connector_id,
        fault_code=fault_event.fault_code,
        priority=fault_event.priority,
        description=f"Auto-genereret: {fault_event.fault_code} paa {fault_event.charger_serial}"
    )

    logger.warning("IncidentCreated: id=%s connector=%s fault=%s priority=%s",
                   incident_id, fault_event.connector_id, fault_event.fault_code, fault_event.priority)

    return jsonify({"message": "Telemetri modtaget – fejl detekteret, incident oprettet",
                    "connector_id": connector_id, "status": reading.status, "fault_detected": True,
                    "incident_id": incident_id, "fault_code": fault_event.fault_code,
                    "priority": fault_event.priority}), 201

@api.route("/telemetry", methods=["GET"])
@require_api_key
def get_telemetry():
    """
    Hent alle telemetrimaelinger
    ---
    tags:
      - Telemetry
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
    responses:
      200:
        description: Liste af telemetrimaelinger
    """
    return jsonify(repo.get_all_telemetry())

@api.route("/incidents", methods=["GET"])
@require_api_key
def get_incidents():
    """
    Hent alle incidents
    ---
    tags:
      - Incidents
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
    responses:
      200:
        description: Liste af incidents
    """
    return jsonify(repo.get_incidents())

@api.route("/incidents/<int:incident_id>", methods=["GET"])
@require_api_key
def get_incident(incident_id):
    """
    Hent et incident
    ---
    tags:
      - Incidents
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
      - name: incident_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Incident
      404:
        description: Ikke fundet
    """
    incident = repo.get_incident_by_id(incident_id)
    if not incident:
        return error_response("Incident ikke fundet", 404)
    return jsonify(incident)

@api.route("/incidents/<int:incident_id>/resolve", methods=["PATCH"])
@require_api_key
def resolve_incident(incident_id):
    """
    Marker incident som loest
    ---
    tags:
      - Incidents
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
      - name: incident_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Incident loest
      404:
        description: Ikke fundet
    """
    incident = repo.get_incident_by_id(incident_id)
    if not incident:
        return error_response("Incident ikke fundet", 404)
    repo.resolve_incident(incident_id)
    logger.info("IncidentResolved: id=%s connector=%s", incident_id, incident["connector_id"])
    return jsonify(repo.get_incident_by_id(incident_id))

@api.route("/analytics/faults", methods=["GET"])
@require_api_key
def analytics_faults():
    """
    Fejlopsummering til Power BI
    ---
    tags:
      - Analytics
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
    responses:
      200:
        description: Fejlopsummering
    """
    return jsonify(repo.get_fault_summary())

@api.route("/analytics/uptime", methods=["GET"])
@require_api_key
def analytics_uptime():
    """
    Oppetid per ladestander til Power BI
    ---
    tags:
      - Analytics
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
    responses:
      200:
        description: Oppetid
    """
    return jsonify(repo.get_uptime_summary())

@api.route("/connectors/<int:connector_id>/predict", methods=["GET"])
@require_api_key
def predict_maintenance(connector_id):
    """
    Predictive maintenance risikovurdering
    ---
    tags:
      - Analytics
    parameters:
      - in: header
        name: X-API-Key
        required: true
        type: string
      - name: connector_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Risikovurdering
      404:
        description: Ingen maalinger fundet
    """
    readings = repo.get_telemetry_by_connector(connector_id, limit=50)
    if not readings:
        return error_response("Ingen telemetrimaalinger fundet", 404)
    return jsonify(predictive_service.analyse(connector_id, readings))

# Power BI endpoints – ingen API-nøgle krævet (til eksamen/demo)
@api.route("/powerbi/faults", methods=["GET"])
def powerbi_faults():
    return analytics_faults()

@api.route("/powerbi/uptime", methods=["GET"])
def powerbi_uptime():
    return analytics_uptime()
