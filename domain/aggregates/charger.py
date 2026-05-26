from dataclasses import dataclass, field
from datetime import datetime
from domain.entities.connector import Connector

@dataclass
class Charger:
    id: int
    serial_number: str
    model: str
    location: str
    status: str
    connectors: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_connector(self, connector_number: int):
        return next((c for c in self.connectors if c.connector_number == connector_number), None)

    def update_status(self) -> None:
        if any(c.is_faulted() for c in self.connectors):
            self.status = "faulted"
        elif all(c.status == "available" for c in self.connectors):
            self.status = "available"
        else:
            self.status = "occupied"
        self.updated_at = datetime.utcnow()

    def has_faulted_connectors(self) -> bool:
        return any(c.is_faulted() for c in self.connectors)
