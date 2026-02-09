"""
AgentMedic Cache
================
Simple in-memory cache with TTL.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class Cache:
    """In-memory cache with TTL."""
    
    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._data: Dict[str, CacheEntry] = {}
    
    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        if time.time() > entry.expires_at:
            del self._data[key]
            return None
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        ttl = ttl or self.default_ttl
        self._data[key] = CacheEntry(value=value, expires_at=time.time() + ttl)
    
    def delete(self, key: str):
        self._data.pop(key, None)
    
    def clear(self):
        self._data.clear()
    
    def cleanup(self):
        now = time.time()
        expired = [k for k, v in self._data.items() if now > v.expires_at]
        for k in expired:
            del self._data[k]


_cache = None

def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache
