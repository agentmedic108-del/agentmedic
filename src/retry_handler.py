"""
AgentMedic Retry Handler
========================
Configurable retry logic with exponential backoff.
"""

import time
import random
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar, Any
from functools import wraps

T = TypeVar('T')


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryError(Exception):
    """Raised when all retry attempts fail."""
    def __init__(self, message: str, attempts: int, last_error: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and optional jitter."""
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        delay = delay * (0.5 + random.random())
    
    return delay


def retry(config: Optional[RetryConfig] = None):
    """Decorator for retry with exponential backoff."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        time.sleep(delay)
            
            raise RetryError(
                f"Failed after {config.max_attempts} attempts",
                config.max_attempts,
                last_error
            )
        return wrapper
    return decorator


async def retry_async(
    func: Callable[..., Any],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """Async retry helper."""
    import asyncio
    
    if config is None:
        config = RetryConfig()
    
    last_error = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < config.max_attempts - 1:
                delay = calculate_delay(attempt, config)
                await asyncio.sleep(delay)
    
    raise RetryError(
        f"Failed after {config.max_attempts} attempts",
        config.max_attempts,
        last_error
    )


# Preset configs
AGGRESSIVE_RETRY = RetryConfig(max_attempts=5, base_delay=0.5, max_delay=30)
GENTLE_RETRY = RetryConfig(max_attempts=3, base_delay=2.0, max_delay=120)
RPC_RETRY = RetryConfig(max_attempts=4, base_delay=1.0, max_delay=15, jitter=True)
