from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Connector:
    id: int
    charger_id: int
    connector_number: int
    type: str
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    VALID_STATUSES = {"available","occupied","faulted","offline","unknown"}

    def update_status(self, new_status: str) -> None:
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Ugyldig status: {new_status}")
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def is_faulted(self) -> bool:
        return self.status in ("faulted","offline")
