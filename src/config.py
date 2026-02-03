"""
AgentMedic Configuration
========================
Central configuration for agent monitoring system.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

# Solana RPC endpoints
SOLANA_DEVNET_RPC = "https://api.devnet.solana.com"
SOLANA_MAINNET_RPC = "https://api.mainnet-beta.solana.com"  # Read-only!

# Default monitoring intervals (seconds)
class Intervals:
    DEFAULT = 600        # 10 minutes
    INCIDENT = 120       # 2 minutes during active incident
    STABLE = 1800        # 30 minutes when healthy for >30min

class AgentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"

class IncidentSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AgentConfig:
    """Configuration for a monitored agent."""
    name: str
    process_name: Optional[str] = None  # systemd/docker service name
    health_endpoint: Optional[str] = None  # HTTP health check URL
    log_path: Optional[str] = None
    solana_address: Optional[str] = None  # Agent's Solana address (devnet)
    restart_command: Optional[str] = None
    max_restarts: int = 3
    restart_backoff_seconds: int = 60
    tags: List[str] = field(default_factory=list)

@dataclass 
class MonitoringConfig:
    """Global monitoring configuration."""
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    solana_rpc: str = SOLANA_DEVNET_RPC
    check_interval: int = Intervals.DEFAULT
    incident_interval: int = Intervals.INCIDENT
    stable_interval: int = Intervals.STABLE
    stable_threshold_minutes: int = 30
    log_dir: str = "logs"
    
    # Safety: never interact with mainnet beyond read-only queries
    mainnet_read_only: bool = True

# Default configuration instance
config = MonitoringConfig()

def register_agent(
    name: str,
    process_name: Optional[str] = None,
    health_endpoint: Optional[str] = None,
    **kwargs
) -> AgentConfig:
    """Register an agent for monitoring."""
    agent = AgentConfig(
        name=name,
        process_name=process_name,
        health_endpoint=health_endpoint,
        **kwargs
    )
    config.agents[name] = agent
    return agent

def get_agent(name: str) -> Optional[AgentConfig]:
    """Get agent configuration by name."""
    return config.agents.get(name)

def list_agents() -> List[str]:
    """List all registered agent names."""
    return list(config.agents.keys())
