from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Incident:
    id: int
    connector_id: int
    fault_code: str
    priority: str
    status: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None

    def resolve(self) -> None:
        if self.status == "resolved":
            raise ValueError(f"Incident {self.id} er allerede resolved")
        self.status = "resolved"
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_open(self) -> bool:
        return self.status == "open"
