"""
AgentMedic Notification System
==============================
Send alerts through various channels.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class NotificationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    CONSOLE = "console"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Notification:
    level: NotificationLevel
    title: str
    message: str
    agent_id: Optional[str] = None
    incident_id: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "agent_id": self.agent_id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp
        }


class NotificationManager:
    """Manage and send notifications."""
    
    def __init__(self):
        self.channels = [NotificationChannel.CONSOLE]
        self.history = []
    
    def send(self, notification: Notification):
        """Send notification through configured channels."""
        self.history.append(notification)
        
        for channel in self.channels:
            if channel == NotificationChannel.CONSOLE:
                self._send_console(notification)
            elif channel == NotificationChannel.LOG:
                self._send_log(notification)
    
    def _send_console(self, n: Notification):
        icons = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
        icon = icons.get(n.level.value, "📢")
        print(f"{icon} [{n.level.value.upper()}] {n.title}")
        print(f"   {n.message}")
        if n.agent_id:
            print(f"   Agent: {n.agent_id}")
    
    def _send_log(self, n: Notification):
        import logging
        level = {"info": logging.INFO, "warning": logging.WARNING, "critical": logging.CRITICAL}
        logging.log(level.get(n.level.value, logging.INFO), f"{n.title}: {n.message}")
    
    def alert(self, title: str, message: str, level: NotificationLevel = NotificationLevel.WARNING, **kwargs):
        """Quick alert helper."""
        n = Notification(level=level, title=title, message=message, **kwargs)
        self.send(n)


# Global instance
_manager: Optional[NotificationManager] = None

def get_notifier() -> NotificationManager:
    global _manager
    if _manager is None:
        _manager = NotificationManager()
    return _manager


def alert(title: str, message: str, level: str = "warning", **kwargs):
    """Quick alert function."""
    lvl = NotificationLevel(level)
    get_notifier().alert(title, message, lvl, **kwargs)
