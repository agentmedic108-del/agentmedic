"""
AgentMedic Agent Registry
=========================
Track and manage monitored agents.
Simple in-memory registry with persistence support.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AgentStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


@dataclass
class MonitoredAgent:
    agent_id: str
    name: str
    process_name: Optional[str] = None
    wallet_address: Optional[str] = None
    registered_at: str = ""
    last_check: str = ""
    status: AgentStatus = AgentStatus.UNKNOWN
    incident_count: int = 0
    recovery_count: int = 0
    
    def __post_init__(self):
        if not self.registered_at:
            self.registered_at = datetime.now(timezone.utc).isoformat()


class AgentRegistry:
    """Central registry for all monitored agents."""
    
    def __init__(self, persist_path: Optional[str] = None):
        self.agents: Dict[str, MonitoredAgent] = {}
        self.persist_path = persist_path
        if persist_path:
            self._load()
    
    def register(self, agent_id: str, name: str, **kwargs) -> MonitoredAgent:
        """Register a new agent for monitoring."""
        agent = MonitoredAgent(agent_id=agent_id, name=name, **kwargs)
        self.agents[agent_id] = agent
        self._save()
        return agent
    
    def get(self, agent_id: str) -> Optional[MonitoredAgent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_all(self) -> List[MonitoredAgent]:
        """List all registered agents."""
        return list(self.agents.values())
    
    def list_by_status(self, status: AgentStatus) -> List[MonitoredAgent]:
        """List agents with specific status."""
        return [a for a in self.agents.values() if a.status == status]
    
    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status."""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_check = datetime.now(timezone.utc).isoformat()
            self._save()
            return True
        return False
    
    def record_incident(self, agent_id: str) -> bool:
        """Record an incident for an agent."""
        if agent_id in self.agents:
            self.agents[agent_id].incident_count += 1
            self._save()
            return True
        return False
    
    def record_recovery(self, agent_id: str) -> bool:
        """Record a successful recovery."""
        if agent_id in self.agents:
            self.agents[agent_id].recovery_count += 1
            self._save()
            return True
        return False
    
    def remove(self, agent_id: str) -> bool:
        """Remove agent from registry."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        agents = list(self.agents.values())
        return {
            "total": len(agents),
            "healthy": len([a for a in agents if a.status == AgentStatus.HEALTHY]),
            "warning": len([a for a in agents if a.status == AgentStatus.WARNING]),
            "critical": len([a for a in agents if a.status == AgentStatus.CRITICAL]),
            "offline": len([a for a in agents if a.status == AgentStatus.OFFLINE]),
            "total_incidents": sum(a.incident_count for a in agents),
            "total_recoveries": sum(a.recovery_count for a in agents),
        }
    
    def _save(self):
        """Persist registry to file."""
        if not self.persist_path:
            return
        data = {k: asdict(v) for k, v in self.agents.items()}
        for k in data:
            data[k]['status'] = data[k]['status'].value
        with open(self.persist_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load registry from file."""
        if not self.persist_path:
            return
        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
            for k, v in data.items():
                v['status'] = AgentStatus(v['status'])
                self.agents[k] = MonitoredAgent(**v)
        except FileNotFoundError:
            pass


# Global registry instance
_registry: Optional[AgentRegistry] = None

def get_registry(persist_path: str = "agent_registry.json") -> AgentRegistry:
    """Get or create global registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry(persist_path)
    return _registry
