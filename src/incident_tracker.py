"""
AgentMedic Incident Tracker
===========================
Track and manage incidents across monitored agents.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enum import Enum
import json


class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class Incident:
    id: str
    agent_id: str
    incident_type: str
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    severity: str = "medium"
    created_at: str = ""
    resolved_at: Optional[str] = None
    recovery_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def resolve(self):
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc).isoformat()


class IncidentTracker:
    """Track all incidents."""
    
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self._counter = 0
    
    def create(self, agent_id: str, incident_type: str, description: str, severity: str = "medium") -> Incident:
        self._counter += 1
        inc_id = f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._counter:04d}"
        
        incident = Incident(
            id=inc_id,
            agent_id=agent_id,
            incident_type=incident_type,
            description=description,
            severity=severity
        )
        self.incidents[inc_id] = incident
        return incident
    
    def get(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)
    
    def get_open(self) -> List[Incident]:
        return [i for i in self.incidents.values() if i.status in (IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.RECOVERING)]
    
    def resolve(self, incident_id: str) -> bool:
        if incident_id in self.incidents:
            self.incidents[incident_id].resolve()
            return True
        return False
    
    def get_stats(self) -> Dict:
        incidents = list(self.incidents.values())
        return {
            "total": len(incidents),
            "open": len([i for i in incidents if i.status == IncidentStatus.OPEN]),
            "resolved": len([i for i in incidents if i.status == IncidentStatus.RESOLVED]),
            "escalated": len([i for i in incidents if i.status == IncidentStatus.ESCALATED]),
        }


_tracker = None

def get_tracker() -> IncidentTracker:
    global _tracker
    if _tracker is None:
        _tracker = IncidentTracker()
    return _tracker
