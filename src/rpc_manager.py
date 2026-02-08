"""
AgentMedic RPC Manager
======================
Manage multiple Solana RPC endpoints with failover.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone
import random


@dataclass 
class RPCEndpoint:
    url: str
    name: str
    healthy: bool = True
    last_check: str = ""
    latency_ms: float = 0
    failure_count: int = 0


class RPCManager:
    """Manage RPC endpoints with health tracking and failover."""
    
    DEVNET_ENDPOINTS = [
        ("https://api.devnet.solana.com", "solana-devnet"),
    ]
    
    MAINNET_ENDPOINTS = [
        ("https://api.mainnet-beta.solana.com", "solana-mainnet"),
    ]
    
    def __init__(self, use_mainnet: bool = False):
        endpoints = self.MAINNET_ENDPOINTS if use_mainnet else self.DEVNET_ENDPOINTS
        self.endpoints = [RPCEndpoint(url=url, name=name) for url, name in endpoints]
        self.current_idx = 0
    
    def get_current(self) -> RPCEndpoint:
        return self.endpoints[self.current_idx]
    
    def get_healthy(self) -> List[RPCEndpoint]:
        return [e for e in self.endpoints if e.healthy]
    
    def mark_unhealthy(self, url: str):
        for e in self.endpoints:
            if e.url == url:
                e.healthy = False
                e.failure_count += 1
                break
        self._failover()
    
    def mark_healthy(self, url: str, latency_ms: float = 0):
        for e in self.endpoints:
            if e.url == url:
                e.healthy = True
                e.latency_ms = latency_ms
                e.last_check = datetime.now(timezone.utc).isoformat()
                break
    
    def _failover(self):
        healthy = self.get_healthy()
        if healthy:
            self.current_idx = self.endpoints.index(healthy[0])
    
    def add_endpoint(self, url: str, name: str):
        self.endpoints.append(RPCEndpoint(url=url, name=name))
    
    def get_stats(self) -> dict:
        return {
            "total": len(self.endpoints),
            "healthy": len(self.get_healthy()),
            "current": self.get_current().name,
            "endpoints": [{"name": e.name, "healthy": e.healthy, "latency": e.latency_ms} for e in self.endpoints]
        }


_manager: Optional[RPCManager] = None

def get_rpc_manager(use_mainnet: bool = False) -> RPCManager:
    global _manager
    if _manager is None:
        _manager = RPCManager(use_mainnet=use_mainnet)
    return _manager
