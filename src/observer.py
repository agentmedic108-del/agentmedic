"""
Observer Module
===============
Monitors registered agents for health status.
Checks: process state, health endpoints, resource usage, Solana transactions.
"""

import subprocess
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import AgentConfig, AgentStatus, config, get_agent, list_agents
import solana_rpc


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    agent_name: str
    timestamp: str
    status: AgentStatus
    checks: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """Overall system status."""
    timestamp: str
    agents: Dict[str, HealthCheckResult]
    solana_rpc: solana_rpc.RPCHealth
    active_incidents: int = 0


def check_process_running(process_name: str) -> Dict[str, Any]:
    """Check if a process is running via systemctl or pgrep."""
    result = {"running": False, "method": None, "details": None}
    
    # Try systemctl first
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", process_name],
            capture_output=True, text=True, timeout=10
        )
        if proc.stdout.strip() == "active":
            result["running"] = True
            result["method"] = "systemctl"
            return result
    except Exception:
        pass
    
    # Try pgrep with -x for exact process name match (not full command line)
    try:
        proc = subprocess.run(
            ["pgrep", "-x", process_name],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 0 and proc.stdout.strip():
            result["running"] = True
            result["method"] = "pgrep"
            result["details"] = {"pids": proc.stdout.strip().split("\n")}
            return result
    except Exception:
        pass
    
    # Try docker
    try:
        proc = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={process_name}"],
            capture_output=True, text=True, timeout=10
        )
        if proc.stdout.strip():
            result["running"] = True
            result["method"] = "docker"
            result["details"] = {"container_id": proc.stdout.strip()}
            return result
    except Exception:
        pass
    
    return result


def check_health_endpoint(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Check an HTTP health endpoint."""
    result = {"healthy": False, "status_code": None, "latency_ms": None, "error": None}
    
    try:
        start = time.time()
        proc = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        latency = (time.time() - start) * 1000
        
        status_code = int(proc.stdout.strip()) if proc.stdout.strip().isdigit() else 0
        result["status_code"] = status_code
        result["latency_ms"] = round(latency, 2)
        result["healthy"] = 200 <= status_code < 300
        
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_recent_transactions(
    address: str, 
    limit: int = 5
) -> Dict[str, Any]:
    """Check recent transactions for failures."""
    result = {
        "total_checked": 0,
        "successful": 0,
        "failed": 0,
        "failures": []
    }
    
    signatures = solana_rpc.get_signatures_for_address(address, limit)
    
    for sig_info in signatures:
        result["total_checked"] += 1
        if sig_info.get("err"):
            result["failed"] += 1
            result["failures"].append({
                "signature": sig_info.get("signature"),
                "error": str(sig_info.get("err")),
                "slot": sig_info.get("slot")
            })
        else:
            result["successful"] += 1
    
    return result


def check_agent(agent: AgentConfig) -> HealthCheckResult:
    """Perform all health checks for a single agent."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    checks = {}
    errors = []
    metrics = {}
    
    # Process check
    if agent.process_name:
        proc_result = check_process_running(agent.process_name)
        checks["process"] = proc_result
        if not proc_result["running"]:
            errors.append(f"Process '{agent.process_name}' not running")
    
    # Health endpoint check
    if agent.health_endpoint:
        health_result = check_health_endpoint(agent.health_endpoint)
        checks["health_endpoint"] = health_result
        if not health_result["healthy"]:
            errors.append(f"Health endpoint unhealthy: {health_result.get('error') or health_result.get('status_code')}")
        if health_result.get("latency_ms"):
            metrics["endpoint_latency_ms"] = health_result["latency_ms"]
    
    # Solana transaction check
    if agent.solana_address:
        tx_result = check_recent_transactions(agent.solana_address)
        checks["transactions"] = tx_result
        if tx_result["failed"] > 0:
            errors.append(f"{tx_result['failed']} failed transactions detected")
        metrics["tx_success_rate"] = (
            tx_result["successful"] / tx_result["total_checked"] 
            if tx_result["total_checked"] > 0 else 1.0
        )
    
    # Determine overall status
    if not checks:
        status = AgentStatus.UNKNOWN
    elif errors:
        # Critical if process is down, degraded otherwise
        if any("not running" in e for e in errors):
            status = AgentStatus.FAILED
        else:
            status = AgentStatus.DEGRADED
    else:
        status = AgentStatus.HEALTHY
    
    return HealthCheckResult(
        agent_name=agent.name,
        timestamp=timestamp,
        status=status,
        checks=checks,
        errors=errors,
        metrics=metrics
    )


def check_all_agents() -> Dict[str, HealthCheckResult]:
    """Check all registered agents."""
    results = {}
    for name in list_agents():
        agent = get_agent(name)
        if agent:
            results[name] = check_agent(agent)
    return results


def get_system_status() -> SystemStatus:
    """Get overall system status including all agents and Solana RPC."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    agent_results = check_all_agents()
    rpc_health = solana_rpc.devnet_health()
    
    active_incidents = sum(
        1 for r in agent_results.values() 
        if r.status in (AgentStatus.FAILED, AgentStatus.DEGRADED)
    )
    
    if not rpc_health.healthy:
        active_incidents += 1
    
    return SystemStatus(
        timestamp=timestamp,
        agents=agent_results,
        solana_rpc=rpc_health,
        active_incidents=active_incidents
    )
