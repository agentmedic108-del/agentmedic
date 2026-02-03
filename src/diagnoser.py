"""
Diagnoser Module
================
Analyzes health check results to determine root causes of failures.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

from config import AgentStatus, IncidentSeverity
from observer import HealthCheckResult, SystemStatus
import solana_rpc


class IncidentType(Enum):
    PROCESS_CRASH = "process_crash"
    PROCESS_HANG = "process_hang"
    HEALTH_ENDPOINT_FAILURE = "health_endpoint_failure"
    RPC_RATE_LIMITED = "rpc_rate_limited"
    RPC_UNAVAILABLE = "rpc_unavailable"
    TRANSACTION_FAILURES = "transaction_failures"
    HIGH_LATENCY = "high_latency"
    UNKNOWN = "unknown"


@dataclass
class Incident:
    """Represents a diagnosed incident."""
    id: str
    timestamp: str
    agent_name: Optional[str]
    incident_type: IncidentType
    severity: IncidentSeverity
    description: str
    evidence: dict
    suggested_actions: List[str]
    requires_human: bool = False


class Diagnoser:
    """Analyzes system status to identify and classify incidents."""
    
    def __init__(self):
        self.incident_counter = 0
    
    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        self.incident_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"INC-{timestamp}-{self.incident_counter:04d}"
    
    def diagnose_agent(self, result: HealthCheckResult) -> List[Incident]:
        """Diagnose issues for a single agent."""
        incidents = []
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if result.status == AgentStatus.HEALTHY:
            return incidents
        
        checks = result.checks
        
        # Process crash detection
        if "process" in checks and not checks["process"].get("running"):
            incidents.append(Incident(
                id=self._generate_incident_id(),
                timestamp=timestamp,
                agent_name=result.agent_name,
                incident_type=IncidentType.PROCESS_CRASH,
                severity=IncidentSeverity.CRITICAL,
                description=f"Agent '{result.agent_name}' process is not running",
                evidence={"process_check": checks["process"]},
                suggested_actions=[
                    f"Restart the agent process",
                    "Check system logs for crash reason",
                    "Verify sufficient system resources"
                ],
                requires_human=False
            ))
        
        # Health endpoint failure
        if "health_endpoint" in checks:
            he = checks["health_endpoint"]
            if not he.get("healthy"):
                if he.get("error") == "Timeout":
                    incident_type = IncidentType.PROCESS_HANG
                    description = f"Agent '{result.agent_name}' health endpoint timed out (possible hang)"
                else:
                    incident_type = IncidentType.HEALTH_ENDPOINT_FAILURE
                    description = f"Agent '{result.agent_name}' health endpoint returned {he.get('status_code')}"
                
                incidents.append(Incident(
                    id=self._generate_incident_id(),
                    timestamp=timestamp,
                    agent_name=result.agent_name,
                    incident_type=incident_type,
                    severity=IncidentSeverity.WARNING if incident_type == IncidentType.HIGH_LATENCY else IncidentSeverity.CRITICAL,
                    description=description,
                    evidence={"health_endpoint": he},
                    suggested_actions=[
                        "Check agent logs for errors",
                        "Restart if unresponsive",
                        "Verify network connectivity"
                    ],
                    requires_human=False
                ))
            elif he.get("latency_ms", 0) > 5000:  # High latency threshold
                incidents.append(Incident(
                    id=self._generate_incident_id(),
                    timestamp=timestamp,
                    agent_name=result.agent_name,
                    incident_type=IncidentType.HIGH_LATENCY,
                    severity=IncidentSeverity.WARNING,
                    description=f"Agent '{result.agent_name}' responding slowly ({he['latency_ms']}ms)",
                    evidence={"latency_ms": he["latency_ms"]},
                    suggested_actions=[
                        "Monitor for further degradation",
                        "Check system resource usage",
                        "Consider restart if persists"
                    ],
                    requires_human=False
                ))
        
        # Transaction failures
        if "transactions" in checks:
            tx = checks["transactions"]
            if tx.get("failed", 0) > 0:
                # Analyze failure types
                failures = tx.get("failures", [])
                
                incidents.append(Incident(
                    id=self._generate_incident_id(),
                    timestamp=timestamp,
                    agent_name=result.agent_name,
                    incident_type=IncidentType.TRANSACTION_FAILURES,
                    severity=IncidentSeverity.WARNING,
                    description=f"Agent '{result.agent_name}' has {tx['failed']} failed transactions",
                    evidence={"transaction_check": tx},
                    suggested_actions=[
                        "Investigate transaction failure reasons",
                        "Check account balances (devnet SOL)",
                        "Verify program IDs are correct",
                        "Check for RPC issues"
                    ],
                    requires_human=True  # Transaction failures often need investigation
                ))
        
        return incidents
    
    def diagnose_rpc(self, rpc_health: solana_rpc.RPCHealth) -> List[Incident]:
        """Diagnose RPC-related issues."""
        incidents = []
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        if not rpc_health.healthy:
            error_msg = rpc_health.error or "Unknown error"
            
            # Check if rate limited
            if "429" in error_msg or "rate" in error_msg.lower():
                incident_type = IncidentType.RPC_RATE_LIMITED
                description = "Solana RPC rate limited"
                actions = [
                    "Apply cooldown period",
                    "Switch to backup RPC endpoint",
                    "Reduce request frequency"
                ]
            else:
                incident_type = IncidentType.RPC_UNAVAILABLE
                description = f"Solana RPC unavailable: {error_msg}"
                actions = [
                    "Switch to backup RPC endpoint",
                    "Wait and retry",
                    "Check Solana network status"
                ]
            
            incidents.append(Incident(
                id=self._generate_incident_id(),
                timestamp=timestamp,
                agent_name=None,  # System-wide issue
                incident_type=incident_type,
                severity=IncidentSeverity.CRITICAL,
                description=description,
                evidence={"rpc_health": {
                    "healthy": rpc_health.healthy,
                    "error": rpc_health.error,
                    "latency_ms": rpc_health.latency_ms
                }},
                suggested_actions=actions,
                requires_human=False
            ))
        elif rpc_health.latency_ms and rpc_health.latency_ms > 2000:
            incidents.append(Incident(
                id=self._generate_incident_id(),
                timestamp=timestamp,
                agent_name=None,
                incident_type=IncidentType.HIGH_LATENCY,
                severity=IncidentSeverity.WARNING,
                description=f"Solana RPC high latency ({rpc_health.latency_ms}ms)",
                evidence={"latency_ms": rpc_health.latency_ms},
                suggested_actions=[
                    "Monitor for further degradation",
                    "Consider switching RPC endpoint"
                ],
                requires_human=False
            ))
        
        return incidents
    
    def analyze(self, status: SystemStatus) -> List[Incident]:
        """Analyze full system status and return all incidents."""
        incidents = []
        
        # Diagnose each agent
        for agent_result in status.agents.values():
            incidents.extend(self.diagnose_agent(agent_result))
        
        # Diagnose RPC
        incidents.extend(self.diagnose_rpc(status.solana_rpc))
        
        return incidents


# Global diagnoser instance
diagnoser = Diagnoser()

def analyze(status: SystemStatus) -> List[Incident]:
    """Convenience function for analysis."""
    return diagnoser.analyze(status)
