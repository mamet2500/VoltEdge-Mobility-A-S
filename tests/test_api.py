import pytest
from unittest.mock import MagicMock, patch
from domain.value_objects.telemetry_reading import TelemetryReading
from domain.services.fault_detection import FaultDetectionService
from domain.services.predictive_maintenance import PredictiveMaintenanceService

API_KEY = "voltedge-dev-key"
HEADERS = {"X-API-Key": API_KEY}

def test_telemetry_reading_valid():
    reading = TelemetryReading(connector_id=1, voltage=230.0, current_amp=16.0, power_kw=11.0, status="available")
    assert reading.voltage == 230.0
    assert reading.status == "available"

def test_telemetry_reading_negative_voltage_raises():
    with pytest.raises(ValueError):
        TelemetryReading(connector_id=1, voltage=-10.0, current_amp=16.0, power_kw=11.0, status="available")

def test_telemetry_reading_invalid_status_raises():
    with pytest.raises(ValueError):
        TelemetryReading(connector_id=1, voltage=230.0, current_amp=16.0, power_kw=11.0, status="ugyldig")

def test_fault_detection_no_fault():
    service = FaultDetectionService()
    reading = TelemetryReading(connector_id=1, voltage=230.0, current_amp=16.0, power_kw=11.0, status="available")
    assert service.evaluate(reading, "CHR-001") is None

def test_fault_detection_faulted_status():
    service = FaultDetectionService()
    reading = TelemetryReading(connector_id=1, voltage=230.0, current_amp=16.0, power_kw=0.0, status="faulted", error_code="GroundFailure")
    result = service.evaluate(reading, "CHR-001")
    assert result is not None
    assert result.fault_code == "ground_failure"
    assert result.priority == "high"

def test_fault_detection_undervoltage():
    service = FaultDetectionService()
    reading = TelemetryReading(connector_id=1, voltage=150.0, current_amp=16.0, power_kw=5.0, status="available")
    result = service.evaluate(reading, "CHR-001")
    assert result is not None
    assert result.fault_code == "undervoltage"

def test_fault_detection_overcurrent():
    service = FaultDetectionService()
    reading = TelemetryReading(connector_id=1, voltage=230.0, current_amp=35.0, power_kw=11.0, status="available")
    result = service.evaluate(reading, "CHR-001")
    assert result is not None
    assert result.fault_code == "overcurrent"
    assert result.priority == "high"

def test_predictive_too_few_readings():
    service = PredictiveMaintenanceService()
    result = service.analyse(1, [{"status": "available", "voltage": 230.0, "current_amp": 16.0}])
    assert result["risk_level"] == "low"

def test_predictive_high_fault_rate():
    service = PredictiveMaintenanceService()
    readings = [{"status": "faulted", "voltage": 230.0, "current_amp": 16.0}] * 8 + \
               [{"status": "available", "voltage": 230.0, "current_amp": 16.0}] * 2
    result = service.analyse(1, readings)
    assert result["risk_level"] in ("medium", "high")
