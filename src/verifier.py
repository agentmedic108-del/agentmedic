"""
Verifier Module
===============
Confirms recovery success after actions are taken.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config import get_agent, AgentStatus
from observer import check_agent, check_process_running
from recoverer import RecoveryPlan, RecoveryResult, RecoveryAction, RecoveryStatus
import solana_rpc


@dataclass
class VerificationResult:
    """Result of recovery verification."""
    incident_id: str
    verified: bool
    timestamp: str
    checks_passed: int
    checks_failed: int
    details: dict
    message: str


class Verifier:
    """Verifies that recovery actions were successful."""
    
    def __init__(self, verification_delay_seconds: int = 10):
        self.verification_delay = verification_delay_seconds
    
    def verify(self, plan: RecoveryPlan, result: RecoveryResult) -> VerificationResult:
        """Verify a recovery action was successful."""
        
        # Wait for recovery to take effect
        time.sleep(self.verification_delay)
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Skip verification for certain statuses
        if result.status in (RecoveryStatus.SKIPPED, RecoveryStatus.FAILED):
            return VerificationResult(
                incident_id=plan.incident_id,
                verified=False,
                timestamp=timestamp,
                checks_passed=0,
                checks_failed=0,
                details={"reason": "Recovery was skipped or failed"},
                message="Verification skipped - recovery did not execute"
            )
        
        # Verify based on action type
        if plan.action == RecoveryAction.RESTART_PROCESS:
            return self._verify_restart(plan, timestamp)
        
        elif plan.action == RecoveryAction.SWITCH_RPC:
            return self._verify_rpc_switch(plan, result, timestamp)
        
        elif plan.action == RecoveryAction.APPLY_COOLDOWN:
            return self._verify_cooldown(plan, timestamp)
        
        # Default: assume success if recovery reported success
        return VerificationResult(
            incident_id=plan.incident_id,
            verified=result.status == RecoveryStatus.SUCCESS,
            timestamp=timestamp,
            checks_passed=1 if result.status == RecoveryStatus.SUCCESS else 0,
            checks_failed=0 if result.status == RecoveryStatus.SUCCESS else 1,
            details={"action": plan.action.value},
            message="Verification based on recovery status"
        )
    
    def _verify_restart(self, plan: RecoveryPlan, timestamp: str) -> VerificationResult:
        """Verify a process restart was successful."""
        checks_passed = 0
        checks_failed = 0
        details = {}
        
        agent = get_agent(plan.agent_name) if plan.agent_name else None
        
        if agent and agent.process_name:
            # Check if process is now running
            proc_check = check_process_running(agent.process_name)
            details["process_check"] = proc_check
            
            if proc_check["running"]:
                checks_passed += 1
            else:
                checks_failed += 1
        
        if agent and agent.health_endpoint:
            # Do a full agent health check
            health_result = check_agent(agent)
            details["health_status"] = health_result.status.value
            
            if health_result.status == AgentStatus.HEALTHY:
                checks_passed += 1
            else:
                checks_failed += 1
        
        verified = checks_passed > 0 and checks_failed == 0
        
        return VerificationResult(
            incident_id=plan.incident_id,
            verified=verified,
            timestamp=timestamp,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            details=details,
            message="Process restart verified" if verified else "Process restart verification failed"
        )
    
    def _verify_rpc_switch(self, plan: RecoveryPlan, result: RecoveryResult, timestamp: str) -> VerificationResult:
        """Verify RPC endpoint switch was successful."""
        new_endpoint = result.details.get("new_endpoint", solana_rpc.DEVNET_RPC)
        
        health = solana_rpc.check_rpc_health(new_endpoint)
        
        return VerificationResult(
            incident_id=plan.incident_id,
            verified=health.healthy,
            timestamp=timestamp,
            checks_passed=1 if health.healthy else 0,
            checks_failed=0 if health.healthy else 1,
            details={
                "endpoint": new_endpoint,
                "healthy": health.healthy,
                "latency_ms": health.latency_ms,
                "slot": health.slot
            },
            message="RPC switch verified" if health.healthy else f"RPC still unhealthy: {health.error}"
        )
    
    def _verify_cooldown(self, plan: RecoveryPlan, timestamp: str) -> VerificationResult:
        """Verify cooldown was applied (and RPC is now accessible)."""
        health = solana_rpc.devnet_health()
        
        return VerificationResult(
            incident_id=plan.incident_id,
            verified=health.healthy,
            timestamp=timestamp,
            checks_passed=1 if health.healthy else 0,
            checks_failed=0 if health.healthy else 1,
            details={
                "rpc_healthy": health.healthy,
                "latency_ms": health.latency_ms
            },
            message="Cooldown effective - RPC accessible" if health.healthy else "RPC still rate limited after cooldown"
        )


# Global verifier instance
verifier = Verifier()

def confirm(plan: RecoveryPlan, result: RecoveryResult) -> VerificationResult:
    """Convenience function to verify recovery."""
    return verifier.verify(plan, result)
