import logging
from domain.value_objects.telemetry_reading import TelemetryReading
from domain.events.domain_events import FaultDetected

logger = logging.getLogger(__name__)

class FaultDetectionService:
    MIN_VOLTAGE_V = 180.0
    MAX_CURRENT_A = 32.0

    def evaluate(self, reading, charger_serial):
        fault_code = self._detect_fault(reading)
        if fault_code is None:
            return None
        priority = self._determine_priority(fault_code)
        logger.warning("FaultDetected: connector=%s fault=%s priority=%s", reading.connector_id, fault_code, priority)
        return FaultDetected(connector_id=reading.connector_id, charger_serial=charger_serial, fault_code=fault_code, priority=priority)

    def _detect_fault(self, reading):
        if reading.status == "faulted":
            return self._classify_error_code(reading.error_code)
        if reading.status == "offline":
            return "communication_error"
        if reading.voltage < self.MIN_VOLTAGE_V:
            return "undervoltage"
        if reading.current_amp > self.MAX_CURRENT_A:
            return "overcurrent"
        return None

    def _classify_error_code(self, error_code):
        if not error_code:
            return "unknown_fault"
        mapping = {
            "ConnectorLockFailure": "connector_lock_failure",
            "GroundFailure": "ground_failure",
            "OverCurrentFailure": "overcurrent",
            "UnderVoltage": "undervoltage",
            "OverVoltage": "overvoltage",
        }
        return mapping.get(error_code, "unknown_fault")

    def _determine_priority(self, fault_code):
        if fault_code in ("overcurrent", "ground_failure", "overvoltage"):
            return "high"
        if fault_code in ("undervoltage", "connector_lock_failure", "communication_error"):
            return "medium"
        return "low"
