from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class TelemetryReceived:
    connector_id: int
    charger_serial: str
    voltage: float
    current_amp: float
    power_kw: float
    status: str
    error_code: str | None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class FaultDetected:
    connector_id: int
    charger_serial: str
    fault_code: str
    priority: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class IncidentCreated:
    incident_id: int
    connector_id: int
    fault_code: str
    priority: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(frozen=True)
class IncidentResolved:
    incident_id: int
    connector_id: int
    resolved_at: datetime = field(default_factory=datetime.utcnow)
