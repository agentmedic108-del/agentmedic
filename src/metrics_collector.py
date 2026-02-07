"""
AgentMedic Metrics Collector
============================
Collect and aggregate metrics for monitored agents.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
import json


@dataclass
class AgentMetrics:
    agent_id: str
    uptime_checks: int = 0
    uptime_success: int = 0
    incidents: int = 0
    recoveries: int = 0
    avg_response_ms: float = 0.0
    last_updated: str = ""
    
    @property
    def uptime_pct(self) -> float:
        if self.uptime_checks == 0:
            return 100.0
        return (self.uptime_success / self.uptime_checks) * 100
    
    @property
    def recovery_rate(self) -> float:
        if self.incidents == 0:
            return 100.0
        return (self.recoveries / self.incidents) * 100


class MetricsCollector:
    """Collect metrics across all monitored agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentMetrics] = {}
        self.started_at = datetime.now(timezone.utc).isoformat()
    
    def record_check(self, agent_id: str, success: bool, response_ms: float = 0):
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMetrics(agent_id=agent_id)
        
        m = self.agents[agent_id]
        m.uptime_checks += 1
        if success:
            m.uptime_success += 1
        m.avg_response_ms = (m.avg_response_ms + response_ms) / 2
        m.last_updated = datetime.now(timezone.utc).isoformat()
    
    def record_incident(self, agent_id: str):
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMetrics(agent_id=agent_id)
        self.agents[agent_id].incidents += 1
    
    def record_recovery(self, agent_id: str):
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentMetrics(agent_id=agent_id)
        self.agents[agent_id].recoveries += 1
    
    def get_summary(self) -> Dict:
        total_checks = sum(m.uptime_checks for m in self.agents.values())
        total_success = sum(m.uptime_success for m in self.agents.values())
        total_incidents = sum(m.incidents for m in self.agents.values())
        total_recoveries = sum(m.recoveries for m in self.agents.values())
        
        return {
            "agents_monitored": len(self.agents),
            "total_checks": total_checks,
            "overall_uptime_pct": (total_success / total_checks * 100) if total_checks > 0 else 100,
            "total_incidents": total_incidents,
            "total_recoveries": total_recoveries,
            "recovery_rate_pct": (total_recoveries / total_incidents * 100) if total_incidents > 0 else 100,
            "started_at": self.started_at
        }
    
    def to_json(self) -> str:
        return json.dumps(self.get_summary(), indent=2)


# Global instance
_collector = None

def get_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
