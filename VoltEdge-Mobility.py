from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
import os
import uuid
from dotenv import load_dotenv

from mysqlrepo import MySQLRepository
from fault_detection import FaultDetectionService
from predictive_maintenance import PredictiveMaintenanceService

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["SWAGGER"] = {
    "title": "VoltEdge Monitoring API",
    "uiversion": 3,
}
swagger = Swagger(app)

repo = MySQLRepository(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    database=os.environ.get("DB_NAME", "voltedge_monitoring"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", "")
)

fault_service = FaultDetectionService()
predictive_service = PredictiveMaintenanceService()


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """
    Liveness check
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is running
    """
    return jsonify({"status": "ok", "service": "voltedge-monitoring"})


# ---------------------------------------------------------------------------
# Chargers
# ---------------------------------------------------------------------------

@app.route("/chargers", methods=["GET"])
def get_chargers():
    """
    Get all chargers
    ---
    tags:
      - Chargers
    responses:
      200:
        description: A list of chargers
        schema:
          type: array
          items:
            $ref: '#/definitions/Charger'
    definitions:
      Charger:
        type: object
        properties:
          charger_id:
            type: string
            example: CHR-001
          location_id:
            type: string
            example: LOC-CPH-01
          status:
            type: string
            example: available
          last_seen:
            type: string
            example: "2026-05-20 10:00:00"
      TelemetryReading:
        type: object
        properties:
          id:
            type: string
          charger_id:
            type: string
            example: CHR-001
          connector_id:
            type: string
            example: CON-1
          power_kw:
            type: number
            example: 11.0
          voltage_v:
            type: number
            example: 230.0
          current_a:
            type: number
            example: 16.0
          status:
            type: string
            example: available
          error_code:
            type: string
            example: null
          ts:
            type: string
            example: "2026-05-20 10:00:00"
      Incident:
        type: object
        properties:
          incident_id:
            type: string
          charger_id:
            type: string
            example: CHR-001
          connector_id:
            type: string
            example: CON-1
          fault_code:
            type: string
            example: undervoltage
          priority:
            type: string
            example: high
          status:
            type: string
            example: open
          description:
            type: string
          created_at:
            type: string
            example: "2026-05-20 10:00:01"
          resolved_at:
            type: string
            example: null
    """
    return jsonify(repo.get_chargers())


@app.route("/chargers/<charger_id>", methods=["GET"])
def get_charger(charger_id):
    """
    Get a charger by id
    ---
    tags:
      - Chargers
    parameters:
      - name: charger_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: The charger
        schema:
          $ref: '#/definitions/Charger'
      404:
        description: Charger not found
    """
    charger = repo.get_charger_by_id(charger_id)
    if charger is None:
        return error_response("Charger not found", 404)
    return jsonify(charger)


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@app.route("/telemetry", methods=["POST"])
def create_telemetry():
    """
    Receive telemetry from a charger and evaluate for faults
    ---
    tags:
      - Telemetry
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - charger_id
            - connector_id
            - location_id
            - power_kw
            - voltage_v
            - current_a
            - status
          properties:
            charger_id:
              type: string
            connector_id:
              type: string
            location_id:
              type: string
            power_kw:
              type: number
            voltage_v:
              type: number
            current_a:
              type: number
            status:
              type: string
            error_code:
              type: string
          example:
            charger_id: CHR-001
            connector_id: CON-1
            location_id: LOC-CPH-01
            power_kw: 11.0
            voltage_v: 230.0
            current_a: 16.0
            status: available
            error_code: null
    responses:
      201:
        description: Telemetry received and processed
      400:
        description: Invalid payload
    """
    payload = request.get_json(silent=True)
    required = ["charger_id", "connector_id", "location_id",
                "power_kw", "voltage_v", "current_a", "status"]

    if payload is None or any(k not in payload for k in required):
        return error_response(f"Required fields: {required}", 400)

    charger_id   = payload["charger_id"]
    connector_id = payload["connector_id"]
    location_id  = payload["location_id"]
    power_kw     = float(payload["power_kw"])
    voltage_v    = float(payload["voltage_v"])
    current_a    = float(payload["current_a"])
    status       = payload["status"]
    error_code   = payload.get("error_code")

    # 1. Gem telemetri
    repo.create_telemetry(charger_id, connector_id, power_kw,
                          voltage_v, current_a, status, error_code)

    # 2. Opdater ladestander
    repo.create_charger(charger_id, location_id, status)

    # 3. Kør fault detection
    fault = fault_service.evaluate(
        charger_id, connector_id, status, voltage_v, current_a, error_code
    )

    if fault is None:
        return jsonify({
            "message": "Telemetry received – no fault detected",
            "charger_id": charger_id,
            "status": status,
            "fault_detected": False
        }), 201

    # 4. Opret incident automatisk
    incident_id = str(uuid.uuid4())
    repo.create_incident(
        incident_id=incident_id,
        charger_id=charger_id,
        connector_id=connector_id,
        fault_code=fault["fault_code"],
        priority=fault["priority"],
        description=f"Auto-generated: {fault['fault_code']} detected on {charger_id}"
    )

    return jsonify({
        "message": "Telemetry received – fault detected, incident created",
        "charger_id": charger_id,
        "status": status,
        "fault_detected": True,
        "incident_id": incident_id,
        "fault_code": fault["fault_code"],
        "priority": fault["priority"]
    }), 201


@app.route("/telemetry", methods=["GET"])
def get_telemetry():
    """
    Get all telemetry readings
    ---
    tags:
      - Telemetry
    responses:
      200:
        description: A list of telemetry readings
        schema:
          type: array
          items:
            $ref: '#/definitions/TelemetryReading'
    """
    return jsonify(repo.get_telemetry())


@app.route("/chargers/<charger_id>/telemetry", methods=["GET"])
def get_charger_telemetry(charger_id):
    """
    Get telemetry readings for a specific charger
    ---
    tags:
      - Chargers
    parameters:
      - name: charger_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Telemetry readings for the charger
      404:
        description: No telemetry found
    """
    readings = repo.get_telemetry_by_charger(charger_id)
    if not readings:
        return error_response("No telemetry found for charger", 404)
    return jsonify(readings)


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

@app.route("/incidents", methods=["GET"])
def get_incidents():
    """
    Get all incidents
    ---
    tags:
      - Incidents
    responses:
      200:
        description: A list of incidents
        schema:
          type: array
          items:
            $ref: '#/definitions/Incident'
    """
    return jsonify(repo.get_incidents())


@app.route("/incidents/<incident_id>", methods=["GET"])
def get_incident(incident_id):
    """
    Get an incident by id
    ---
    tags:
      - Incidents
    parameters:
      - name: incident_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: The incident
        schema:
          $ref: '#/definitions/Incident'
      404:
        description: Incident not found
    """
    incident = repo.get_incident_by_id(incident_id)
    if incident is None:
        return error_response("Incident not found", 404)
    return jsonify(incident)


@app.route("/incidents/<incident_id>/resolve", methods=["PATCH"])
def resolve_incident(incident_id):
    """
    Resolve an incident
    ---
    tags:
      - Incidents
    parameters:
      - name: incident_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Incident resolved
      404:
        description: Incident not found
    """
    incident = repo.get_incident_by_id(incident_id)
    if incident is None:
        return error_response("Incident not found", 404)

    repo.resolve_incident(incident_id)
    return jsonify(repo.get_incident_by_id(incident_id))


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@app.route("/analytics/faults", methods=["GET"])
def analytics_faults():
    """
    Fault summary grouped by fault_code – for Power BI
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Fault summary
    """
    return jsonify(repo.get_fault_summary())


@app.route("/analytics/uptime", methods=["GET"])
def analytics_uptime():
    """
    Charger uptime summary – for Power BI
    ---
    tags:
      - Analytics
    responses:
      200:
        description: Uptime per charger
    """
    return jsonify(repo.get_uptime_summary())


@app.route("/chargers/<charger_id>/predict", methods=["GET"])
def predict_maintenance(charger_id):
    """
    Predictive maintenance risk assessment for a charger
    ---
    tags:
      - Analytics
    parameters:
      - name: charger_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Risk assessment result
      404:
        description: No telemetry found for charger
    """
    readings = repo.get_telemetry_by_charger(charger_id, limit=50)
    if not readings:
        return error_response("No telemetry found for charger", 404)

    prediction = predictive_service.analyse(charger_id, readings)
    return jsonify(prediction)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
