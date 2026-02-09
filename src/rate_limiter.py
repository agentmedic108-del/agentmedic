"""
AgentMedic Rate Limiter
=======================
Token bucket rate limiter for API calls.
"""

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class RateLimitConfig:
    tokens_per_second: float = 10.0
    max_tokens: float = 100.0


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.tokens = self.config.max_tokens
        self.last_update = time.time()
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.config.max_tokens,
            self.tokens + elapsed * self.config.tokens_per_second
        )
        self.last_update = now
    
    def acquire(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def wait_and_acquire(self, tokens: float = 1.0) -> float:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0
        
        needed = tokens - self.tokens
        wait_time = needed / self.config.tokens_per_second
        time.sleep(wait_time)
        self._refill()
        self.tokens -= tokens
        return wait_time


_limiters: Dict[str, RateLimiter] = {}

def get_limiter(name: str, config: RateLimitConfig = None) -> RateLimiter:
    if name not in _limiters:
        _limiters[name] = RateLimiter(config)
    return _limiters[name]


RPC_LIMITER = RateLimitConfig(tokens_per_second=5, max_tokens=20)
API_LIMITER = RateLimitConfig(tokens_per_second=2, max_tokens=10)
