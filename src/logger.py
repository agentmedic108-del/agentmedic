"""
Logger Module
=============
Logs incidents, recoveries, and metrics to persistent files.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import config
from observer import SystemStatus, HealthCheckResult
from diagnoser import Incident
from recoverer import RecoveryResult
from verifier import VerificationResult


class Logger:
    """Handles all logging for AgentMedic."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.incident_file = self.log_dir / "incident_report.json"
        self.recovery_file = self.log_dir / "recovery_log.md"
        self.metrics_file = self.log_dir / "metrics.json"
        
        # Initialize files if they don't exist
        self._init_files()
        
        # In-memory metrics
        self.metrics = self._load_metrics()
    
    def _init_files(self):
        """Initialize log files if they don't exist."""
        if not self.incident_file.exists():
            self._write_json(self.incident_file, {"incidents": []})
        
        if not self.recovery_file.exists():
            self.recovery_file.write_text("# Recovery Log\n\n")
        
        if not self.metrics_file.exists():
            self._write_json(self.metrics_file, {
                "started_at": datetime.utcnow().isoformat() + "Z",
                "total_checks": 0,
                "total_incidents": 0,
                "total_recoveries": 0,
                "successful_recoveries": 0,
                "failed_recoveries": 0,
                "uptime_checks": {"healthy": 0, "unhealthy": 0},
                "mttr_samples": [],
                "false_positives": 0
            })
    
    def _write_json(self, path: Path, data: dict):
        """Write JSON to file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _read_json(self, path: Path) -> dict:
        """Read JSON from file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _load_metrics(self) -> dict:
        """Load current metrics."""
        return self._read_json(self.metrics_file)
    
    def _save_metrics(self):
        """Save current metrics."""
        self._write_json(self.metrics_file, self.metrics)
    
    def log_check(self, status: SystemStatus):
        """Log a monitoring check."""
        self.metrics["total_checks"] += 1
        
        # Track uptime
        if status.active_incidents == 0:
            self.metrics["uptime_checks"]["healthy"] += 1
        else:
            self.metrics["uptime_checks"]["unhealthy"] += 1
        
        self._save_metrics()
    
    def log_incident(self, incident: Incident):
        """Log a new incident."""
        data = self._read_json(self.incident_file)
        
        incident_record = {
            "id": incident.id,
            "timestamp": incident.timestamp,
            "agent": incident.agent_name,
            "type": incident.incident_type.value,
            "severity": incident.severity.value,
            "description": incident.description,
            "evidence": incident.evidence,
            "suggested_actions": incident.suggested_actions,
            "requires_human": incident.requires_human,
            "status": "open"
        }
        
        data["incidents"].append(incident_record)
        self._write_json(self.incident_file, data)
        
        self.metrics["total_incidents"] += 1
        self._save_metrics()
    
    def log_recovery(
        self, 
        incident: Incident,
        result: RecoveryResult,
        verification: Optional[VerificationResult] = None
    ):
        """Log a recovery attempt."""
        timestamp = datetime.utcnow()
        
        # Update incident status in incident_report.json
        data = self._read_json(self.incident_file)
        for inc in data["incidents"]:
            if inc["id"] == incident.id:
                inc["status"] = "resolved" if (verification and verification.verified) else "recovery_attempted"
                inc["recovery_result"] = {
                    "action": result.action.value,
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp
                }
                if verification:
                    inc["verification"] = {
                        "verified": verification.verified,
                        "message": verification.message
                    }
                break
        self._write_json(self.incident_file, data)
        
        # Append to recovery_log.md
        with open(self.recovery_file, 'a') as f:
            f.write(f"\n## {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            f.write(f"**Incident:** {incident.id}\n")
            f.write(f"**Type:** {incident.incident_type.value}\n")
            f.write(f"**Agent:** {incident.agent_name or 'System'}\n")
            f.write(f"**Description:** {incident.description}\n\n")
            f.write(f"**Recovery Action:** {result.action.value}\n")
            f.write(f"**Result:** {result.status.value}\n")
            f.write(f"**Message:** {result.message}\n")
            if verification:
                f.write(f"\n**Verification:** {'✅ Verified' if verification.verified else '❌ Not Verified'}\n")
                f.write(f"**Verification Details:** {verification.message}\n")
            f.write(f"\n---\n")
        
        # Update metrics
        self.metrics["total_recoveries"] += 1
        if verification and verification.verified:
            self.metrics["successful_recoveries"] += 1
            # Calculate MTTR if we have timing
            if incident.timestamp and result.timestamp:
                try:
                    start = datetime.fromisoformat(incident.timestamp.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
                    mttr_seconds = (end - start).total_seconds()
                    self.metrics["mttr_samples"].append(mttr_seconds)
                    # Keep only last 100 samples
                    self.metrics["mttr_samples"] = self.metrics["mttr_samples"][-100:]
                except Exception:
                    pass
        else:
            self.metrics["failed_recoveries"] += 1
        
        self._save_metrics()
    
    def log_false_positive(self, incident_id: str):
        """Log a false positive (incident that wasn't real)."""
        self.metrics["false_positives"] += 1
        
        # Update incident status
        data = self._read_json(self.incident_file)
        for inc in data["incidents"]:
            if inc["id"] == incident_id:
                inc["status"] = "false_positive"
                break
        self._write_json(self.incident_file, data)
        
        self._save_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        metrics = self.metrics
        
        total_uptime_checks = metrics["uptime_checks"]["healthy"] + metrics["uptime_checks"]["unhealthy"]
        uptime_percent = (
            metrics["uptime_checks"]["healthy"] / total_uptime_checks * 100
            if total_uptime_checks > 0 else 100.0
        )
        
        mttr_samples = metrics.get("mttr_samples", [])
        avg_mttr = sum(mttr_samples) / len(mttr_samples) if mttr_samples else 0
        
        total_recoveries = metrics["total_recoveries"]
        success_rate = (
            metrics["successful_recoveries"] / total_recoveries * 100
            if total_recoveries > 0 else 100.0
        )
        
        total_incidents = metrics["total_incidents"]
        fp_rate = (
            metrics["false_positives"] / total_incidents * 100
            if total_incidents > 0 else 0.0
        )
        
        return {
            "started_at": metrics.get("started_at"),
            "total_checks": metrics["total_checks"],
            "uptime_percent": round(uptime_percent, 2),
            "total_incidents": total_incidents,
            "total_recoveries": total_recoveries,
            "recovery_success_rate": round(success_rate, 2),
            "mttr_seconds": round(avg_mttr, 2),
            "false_positive_rate": round(fp_rate, 2)
        }


# Global logger instance
logger = Logger(str(Path(__file__).parent.parent / "logs"))

def log_check(status: SystemStatus):
    logger.log_check(status)

def log_incident(incident: Incident):
    logger.log_incident(incident)

def log_recovery(incident: Incident, result: RecoveryResult, verification: Optional[VerificationResult] = None):
    logger.log_recovery(incident, result, verification)

def get_metrics() -> Dict[str, Any]:
    return logger.get_metrics_summary()
