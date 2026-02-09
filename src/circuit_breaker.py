"""
AgentMedic Circuit Breaker
==========================
Prevent cascading failures with circuit breaker pattern.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    

class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
    
    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self._timeout_expired():
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN - allow limited requests
        return True
    
    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close()
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.failure_count >= self.config.failure_threshold:
            self._open()
    
    def _open(self):
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self.success_count = 0
    
    def _close(self):
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
    
    def _timeout_expired(self) -> bool:
        """Check if timeout has expired."""
        if not self.last_failure_time:
            return True
        elapsed = datetime.now(timezone.utc) - self.last_failure_time
        return elapsed.total_seconds() >= self.config.timeout_seconds
    
    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "successes": self.success_count,
            "can_execute": self.can_execute()
        }


# Registry of circuit breakers
_breakers: dict = {}

def get_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, config)
    return _breakers[name]
