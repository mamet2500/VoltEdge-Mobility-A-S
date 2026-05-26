from dataclasses import dataclass

@dataclass(frozen=True)
class TelemetryReading:
    connector_id: int
    voltage: float
    current_amp: float
    power_kw: float
    status: str
    temperature: float | None = None
    error_code: str | None = None

    def __post_init__(self):
        if self.voltage < 0:
            raise ValueError(f"Voltage kan ikke vaere negativ: {self.voltage}")
        if self.current_amp < 0:
            raise ValueError(f"Stroem kan ikke vaere negativ: {self.current_amp}")
        if self.power_kw < 0:
            raise ValueError(f"Effekt kan ikke vaere negativ: {self.power_kw}")
        valid = {"available","occupied","faulted","offline","unknown"}
        if self.status not in valid:
            raise ValueError(f"Ugyldig status: {self.status}")
