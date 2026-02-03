#!/usr/bin/env python3
"""
Alert System
============
Handles notifications and escalations for critical incidents.
Supports multiple channels: console, file, webhook.

SAFETY: No external API calls without explicit configuration.
"""

import json
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from enum import Enum
from pathlib import Path

from config import IncidentSeverity
from diagnoser import Incident


class AlertChannel(Enum):
    CONSOLE = "console"
    FILE = "file"
    WEBHOOK = "webhook"


@dataclass
class AlertConfig:
    """Configuration for an alert channel."""
    channel: AlertChannel
    enabled: bool = True
    min_severity: IncidentSeverity = IncidentSeverity.WARNING
    # Channel-specific settings
    file_path: Optional[str] = None
    webhook_url: Optional[str] = None  # Would need explicit user config


class Alert:
    """Represents an alert to be sent."""
    
    def __init__(
        self,
        incident: Incident,
        title: str,
        message: str,
        severity: IncidentSeverity,
        timestamp: Optional[str] = None
    ):
        self.incident = incident
        self.title = title
        self.message = message
        self.severity = severity
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "agent": self.incident.agent_name,
            "incident_type": self.incident.incident_type.value
        }


class AlertManager:
    """Manages alert routing and delivery."""
    
    def __init__(self):
        self.channels: List[AlertConfig] = [
            AlertConfig(channel=AlertChannel.CONSOLE, enabled=True),
            AlertConfig(
                channel=AlertChannel.FILE, 
                enabled=True,
                file_path="logs/alerts.log"
            )
        ]
        self.alert_history: List[Alert] = []
        self.suppression_window_seconds = 300  # 5 min
    
    def _should_suppress(self, alert: Alert) -> bool:
        """Check if alert should be suppressed (dedup)."""
        cutoff = datetime.utcnow().timestamp() - self.suppression_window_seconds
        
        for hist in self.alert_history:
            if hist.incident.agent_name == alert.incident.agent_name and \
               hist.incident.incident_type == alert.incident.incident_type:
                try:
                    hist_time = datetime.fromisoformat(
                        hist.timestamp.replace("Z", "+00:00")
                    ).timestamp()
                    if hist_time > cutoff:
                        return True
                except:
                    pass
        
        return False
    
    def _send_console(self, alert: Alert):
        """Print alert to console."""
        severity_icons = {
            IncidentSeverity.INFO: "ℹ️",
            IncidentSeverity.WARNING: "⚠️",
            IncidentSeverity.CRITICAL: "🚨"
        }
        icon = severity_icons.get(alert.severity, "•")
        
        print(f"\n{icon} ALERT: {alert.title}")
        print(f"   {alert.message}")
        print(f"   Incident: {alert.incident.id}")
        print(f"   Agent: {alert.incident.agent_name or 'System'}")
        print()
    
    def _send_file(self, alert: Alert, file_path: str):
        """Append alert to log file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'a') as f:
            f.write(json.dumps(alert.to_dict()) + "\n")
    
    def _send_webhook(self, alert: Alert, webhook_url: str):
        """Send alert to webhook (placeholder - needs user config)."""
        # SAFETY: Webhooks disabled by default
        # Would use subprocess curl if enabled
        pass
    
    def send_alert(self, alert: Alert) -> bool:
        """Send an alert through configured channels."""
        
        # Check suppression
        if self._should_suppress(alert):
            return False
        
        sent = False
        for config in self.channels:
            if not config.enabled:
                continue
            
            # Check severity threshold
            severity_order = [IncidentSeverity.INFO, IncidentSeverity.WARNING, IncidentSeverity.CRITICAL]
            if severity_order.index(alert.severity) < severity_order.index(config.min_severity):
                continue
            
            try:
                if config.channel == AlertChannel.CONSOLE:
                    self._send_console(alert)
                    sent = True
                elif config.channel == AlertChannel.FILE and config.file_path:
                    self._send_file(alert, config.file_path)
                    sent = True
                elif config.channel == AlertChannel.WEBHOOK and config.webhook_url:
                    self._send_webhook(alert, config.webhook_url)
                    sent = True
            except Exception as e:
                print(f"Alert delivery failed ({config.channel.value}): {e}")
        
        if sent:
            self.alert_history.append(alert)
            # Keep only recent history
            self.alert_history = self.alert_history[-100:]
        
        return sent
    
    def alert_for_incident(self, incident: Incident) -> bool:
        """Create and send alert for an incident."""
        severity_map = {
            IncidentSeverity.INFO: "Info",
            IncidentSeverity.WARNING: "Warning",
            IncidentSeverity.CRITICAL: "Critical"
        }
        
        alert = Alert(
            incident=incident,
            title=f"[{severity_map[incident.severity]}] {incident.incident_type.value}",
            message=incident.description,
            severity=incident.severity
        )
        
        return self.send_alert(alert)
    
    def alert_human_required(self, incident: Incident, reason: str) -> bool:
        """Send alert when human intervention is required."""
        alert = Alert(
            incident=incident,
            title="🚨 Human Intervention Required",
            message=f"{incident.description}\n\nReason: {reason}",
            severity=IncidentSeverity.CRITICAL
        )
        
        return self.send_alert(alert)


# Global alert manager
alert_manager = AlertManager()

def alert_incident(incident: Incident) -> bool:
    """Convenience function to alert for an incident."""
    return alert_manager.alert_for_incident(incident)

def alert_human_needed(incident: Incident, reason: str) -> bool:
    """Convenience function for human-required alerts."""
    return alert_manager.alert_human_required(incident, reason)
