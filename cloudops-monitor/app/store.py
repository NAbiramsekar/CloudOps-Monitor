from threading import Lock

from app.models import Incident, IncidentCreate, IncidentUpdate


class IncidentStore:
    """Thread-safe in-memory incident store for demo and container deployment."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._lock = Lock()

    def list(self) -> list[Incident]:
        with self._lock:
            return sorted(
                self._incidents.values(),
                key=lambda incident: incident.created_time,
                reverse=True,
            )

    def create(self, payload: IncidentCreate) -> Incident:
        incident = Incident(**payload.model_dump())
        with self._lock:
            self._incidents[incident.incident_id] = incident
        return incident

    def update(self, incident_id: str, payload: IncidentUpdate) -> Incident | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                return None

            updated = incident.model_copy(update=payload.model_dump(exclude_unset=True))
            self._incidents[incident_id] = updated
            return updated

    def delete(self, incident_id: str) -> bool:
        with self._lock:
            return self._incidents.pop(incident_id, None) is not None

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for incident in self._incidents.values() if incident.status != "resolved")


incident_store = IncidentStore()
