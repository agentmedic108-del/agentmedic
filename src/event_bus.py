"""
AgentMedic Event Bus
====================
Simple pub/sub event system for internal communication.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Any
from enum import Enum


class EventType(Enum):
    AGENT_REGISTERED = "agent.registered"
    AGENT_REMOVED = "agent.removed"
    HEALTH_CHECK = "health.check"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"
    INCIDENT_OPENED = "incident.opened"
    INCIDENT_RESOLVED = "incident.resolved"
    RECOVERY_STARTED = "recovery.started"
    RECOVERY_SUCCESS = "recovery.success"
    RECOVERY_FAILED = "recovery.failed"
    ALERT_SENT = "alert.sent"


@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EventBus:
    """Simple event bus for AgentMedic components."""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]
    
    def publish(self, event: Event):
        """Publish an event to all subscribers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Event handler error: {e}")
    
    def emit(self, event_type: EventType, **data):
        """Convenience method to emit an event."""
        self.publish(Event(type=event_type, data=data))
    
    def get_history(self, event_type: EventType = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by type."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]


# Global instance
_bus = None

def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
