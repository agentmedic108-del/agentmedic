"""
Recoverer Module
================
Executes safe recovery actions for diagnosed incidents.
SAFETY: Never signs transactions, never handles funds, never exposes secrets.
"""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

from config import AgentConfig, get_agent
from diagnoser import Incident, IncidentType


class RecoveryAction(Enum):
    RESTART_PROCESS = "restart_process"
    SWITCH_RPC = "switch_rpc"
    APPLY_COOLDOWN = "apply_cooldown"
    CLEAR_CACHE = "clear_cache"
    ALERT_HUMAN = "alert_human"
    NO_ACTION = "no_action"


class RecoveryStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RecoveryPlan:
    """Plan for recovering from an incident."""
    incident_id: str
    action: RecoveryAction
    agent_name: Optional[str]
    parameters: Dict = field(default_factory=dict)
    requires_human: bool = False
    reason: str = ""


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    incident_id: str
    action: RecoveryAction
    status: RecoveryStatus
    timestamp: str
    duration_seconds: float
    message: str
    details: Dict = field(default_factory=dict)


class Recoverer:
    """Executes safe recovery actions."""
    
    def __init__(self):
        # Track restart attempts per agent for backoff
        self.restart_attempts: Dict[str, List[datetime]] = {}
        
        # Backup RPC endpoints
        self.rpc_endpoints = [
            "https://api.devnet.solana.com",
            # Add more devnet endpoints as needed
        ]
        self.current_rpc_index = 0
    
    def _get_restart_count(self, agent_name: str, window_minutes: int = 30) -> int:
        """Get number of restarts in recent time window."""
        if agent_name not in self.restart_attempts:
            return 0
        
        cutoff = datetime.utcnow().timestamp() - (window_minutes * 60)
        recent = [t for t in self.restart_attempts[agent_name] if t.timestamp() > cutoff]
        self.restart_attempts[agent_name] = [datetime.fromtimestamp(t.timestamp()) for t in recent]
        return len(recent)
    
    def _record_restart(self, agent_name: str):
        """Record a restart attempt."""
        if agent_name not in self.restart_attempts:
            self.restart_attempts[agent_name] = []
        self.restart_attempts[agent_name].append(datetime.utcnow())
    
    def plan_action(self, incident: Incident) -> RecoveryPlan:
        """Determine the appropriate recovery action for an incident."""
        
        # If incident already requires human, don't try automated recovery
        if incident.requires_human:
            return RecoveryPlan(
                incident_id=incident.id,
                action=RecoveryAction.ALERT_HUMAN,
                agent_name=incident.agent_name,
                requires_human=True,
                reason=incident.description
            )
        
        # Plan based on incident type
        if incident.incident_type == IncidentType.PROCESS_CRASH:
            agent = get_agent(incident.agent_name) if incident.agent_name else None
            
            if agent:
                restart_count = self._get_restart_count(agent.name)
                if restart_count >= agent.max_restarts:
                    return RecoveryPlan(
                        incident_id=incident.id,
                        action=RecoveryAction.ALERT_HUMAN,
                        agent_name=agent.name,
                        requires_human=True,
                        reason=f"Max restarts ({agent.max_restarts}) exceeded in 30 minutes"
                    )
                
                return RecoveryPlan(
                    incident_id=incident.id,
                    action=RecoveryAction.RESTART_PROCESS,
                    agent_name=agent.name,
                    parameters={
                        "command": agent.restart_command,
                        "process_name": agent.process_name,
                        "backoff_seconds": agent.restart_backoff_seconds * (restart_count + 1)
                    }
                )
        
        elif incident.incident_type == IncidentType.PROCESS_HANG:
            return RecoveryPlan(
                incident_id=incident.id,
                action=RecoveryAction.RESTART_PROCESS,
                agent_name=incident.agent_name,
                parameters={"force": True}
            )
        
        elif incident.incident_type == IncidentType.RPC_RATE_LIMITED:
            return RecoveryPlan(
                incident_id=incident.id,
                action=RecoveryAction.APPLY_COOLDOWN,
                agent_name=None,
                parameters={"cooldown_seconds": 60}
            )
        
        elif incident.incident_type == IncidentType.RPC_UNAVAILABLE:
            return RecoveryPlan(
                incident_id=incident.id,
                action=RecoveryAction.SWITCH_RPC,
                agent_name=None,
                parameters={}
            )
        
        elif incident.incident_type == IncidentType.TRANSACTION_FAILURES:
            # Transaction failures need investigation
            return RecoveryPlan(
                incident_id=incident.id,
                action=RecoveryAction.ALERT_HUMAN,
                agent_name=incident.agent_name,
                requires_human=True,
                reason="Transaction failures require investigation"
            )
        
        # Default: no automated action
        return RecoveryPlan(
            incident_id=incident.id,
            action=RecoveryAction.NO_ACTION,
            agent_name=incident.agent_name,
            reason="No automated recovery available"
        )
    
    def execute(self, plan: RecoveryPlan) -> RecoveryResult:
        """Execute a recovery plan."""
        start_time = time.time()
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        try:
            if plan.action == RecoveryAction.RESTART_PROCESS:
                return self._execute_restart(plan, start_time, timestamp)
            
            elif plan.action == RecoveryAction.SWITCH_RPC:
                return self._execute_switch_rpc(plan, start_time, timestamp)
            
            elif plan.action == RecoveryAction.APPLY_COOLDOWN:
                return self._execute_cooldown(plan, start_time, timestamp)
            
            elif plan.action == RecoveryAction.ALERT_HUMAN:
                return RecoveryResult(
                    incident_id=plan.incident_id,
                    action=plan.action,
                    status=RecoveryStatus.SKIPPED,
                    timestamp=timestamp,
                    duration_seconds=time.time() - start_time,
                    message=f"Human intervention required: {plan.reason}",
                    details={"requires_human": True}
                )
            
            elif plan.action == RecoveryAction.NO_ACTION:
                return RecoveryResult(
                    incident_id=plan.incident_id,
                    action=plan.action,
                    status=RecoveryStatus.SKIPPED,
                    timestamp=timestamp,
                    duration_seconds=time.time() - start_time,
                    message="No action taken",
                    details={}
                )
            
        except Exception as e:
            return RecoveryResult(
                incident_id=plan.incident_id,
                action=plan.action,
                status=RecoveryStatus.FAILED,
                timestamp=timestamp,
                duration_seconds=time.time() - start_time,
                message=f"Recovery failed: {str(e)}",
                details={"error": str(e)}
            )
        
        return RecoveryResult(
            incident_id=plan.incident_id,
            action=plan.action,
            status=RecoveryStatus.SKIPPED,
            timestamp=timestamp,
            duration_seconds=time.time() - start_time,
            message="Unknown action",
            details={}
        )
    
    def _execute_restart(self, plan: RecoveryPlan, start_time: float, timestamp: str) -> RecoveryResult:
        """Execute a process restart."""
        params = plan.parameters
        backoff = params.get("backoff_seconds", 0)
        
        if backoff > 0:
            time.sleep(backoff)
        
        # Try custom restart command first
        if params.get("command"):
            try:
                result = subprocess.run(
                    params["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    self._record_restart(plan.agent_name)
                    return RecoveryResult(
                        incident_id=plan.incident_id,
                        action=plan.action,
                        status=RecoveryStatus.SUCCESS,
                        timestamp=timestamp,
                        duration_seconds=time.time() - start_time,
                        message=f"Restarted '{plan.agent_name}' via custom command",
                        details={"method": "custom_command", "backoff_applied": backoff}
                    )
            except Exception:
                pass
        
        # Try systemctl
        process_name = params.get("process_name", plan.agent_name)
        try:
            result = subprocess.run(
                ["systemctl", "restart", process_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self._record_restart(plan.agent_name)
                return RecoveryResult(
                    incident_id=plan.incident_id,
                    action=plan.action,
                    status=RecoveryStatus.SUCCESS,
                    timestamp=timestamp,
                    duration_seconds=time.time() - start_time,
                    message=f"Restarted '{process_name}' via systemctl",
                    details={"method": "systemctl", "backoff_applied": backoff}
                )
        except Exception:
            pass
        
        # Try docker
        try:
            result = subprocess.run(
                ["docker", "restart", process_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self._record_restart(plan.agent_name)
                return RecoveryResult(
                    incident_id=plan.incident_id,
                    action=plan.action,
                    status=RecoveryStatus.SUCCESS,
                    timestamp=timestamp,
                    duration_seconds=time.time() - start_time,
                    message=f"Restarted '{process_name}' via docker",
                    details={"method": "docker", "backoff_applied": backoff}
                )
        except Exception:
            pass
        
        return RecoveryResult(
            incident_id=plan.incident_id,
            action=plan.action,
            status=RecoveryStatus.FAILED,
            timestamp=timestamp,
            duration_seconds=time.time() - start_time,
            message=f"Failed to restart '{plan.agent_name}' via any method",
            details={"tried": ["custom_command", "systemctl", "docker"]}
        )
    
    def _execute_switch_rpc(self, plan: RecoveryPlan, start_time: float, timestamp: str) -> RecoveryResult:
        """Switch to backup RPC endpoint."""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_endpoints)
        new_rpc = self.rpc_endpoints[self.current_rpc_index]
        
        return RecoveryResult(
            incident_id=plan.incident_id,
            action=plan.action,
            status=RecoveryStatus.SUCCESS,
            timestamp=timestamp,
            duration_seconds=time.time() - start_time,
            message=f"Switched to RPC endpoint: {new_rpc}",
            details={"new_endpoint": new_rpc}
        )
    
    def _execute_cooldown(self, plan: RecoveryPlan, start_time: float, timestamp: str) -> RecoveryResult:
        """Apply a cooldown period."""
        cooldown = plan.parameters.get("cooldown_seconds", 60)
        time.sleep(cooldown)
        
        return RecoveryResult(
            incident_id=plan.incident_id,
            action=plan.action,
            status=RecoveryStatus.SUCCESS,
            timestamp=timestamp,
            duration_seconds=time.time() - start_time,
            message=f"Applied {cooldown}s cooldown",
            details={"cooldown_seconds": cooldown}
        )


# Global recoverer instance
recoverer = Recoverer()

def plan_action(incident: Incident) -> RecoveryPlan:
    return recoverer.plan_action(incident)

def execute(plan: RecoveryPlan) -> RecoveryResult:
    return recoverer.execute(plan)
