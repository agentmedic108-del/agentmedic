"""
AgentMedic Heartbeat Module
===========================
Lightweight heartbeat for 24/7 monitoring without AI tokens.
Designed for local loop execution.
"""

import time
import json
from datetime import datetime, timezone
from typing import Callable, List, Optional
from dataclasses import dataclass


@dataclass
class HeartbeatResult:
    timestamp: str
    checks_passed: int
    checks_failed: int
    alerts: List[str]
    
    @property
    def healthy(self) -> bool:
        return self.checks_failed == 0 and len(self.alerts) == 0


class Heartbeat:
    """Lightweight heartbeat for continuous monitoring."""
    
    def __init__(self, interval_seconds: int = 30):
        self.interval = interval_seconds
        self.checks: List[Callable] = []
        self.on_alert: Optional[Callable] = None
        self.running = False
        self.beat_count = 0
    
    def add_check(self, check_fn: Callable[[], bool], name: str = ""):
        """Add a health check function."""
        self.checks.append((check_fn, name or f"check_{len(self.checks)}"))
    
    def beat(self) -> HeartbeatResult:
        """Execute one heartbeat cycle."""
        self.beat_count += 1
        passed = 0
        failed = 0
        alerts = []
        
        for check_fn, name in self.checks:
            try:
                if check_fn():
                    passed += 1
                else:
                    failed += 1
                    alerts.append(f"{name} failed")
            except Exception as e:
                failed += 1
                alerts.append(f"{name} error: {str(e)[:50]}")
        
        result = HeartbeatResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            checks_passed=passed,
            checks_failed=failed,
            alerts=alerts
        )
        
        if alerts and self.on_alert:
            self.on_alert(result)
        
        return result
    
    def run_loop(self, max_beats: Optional[int] = None):
        """Run continuous heartbeat loop."""
        self.running = True
        beats = 0
        
        while self.running:
            result = self.beat()
            beats += 1
            
            if max_beats and beats >= max_beats:
                break
            
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the heartbeat loop."""
        self.running = False


def create_default_heartbeat() -> Heartbeat:
    """Create heartbeat with default checks."""
    hb = Heartbeat(interval_seconds=30)
    
    # Basic system check
    def check_system():
        import os
        return os.getloadavg()[0] < 10.0
    
    hb.add_check(check_system, "system_load")
    
    return hb


if __name__ == "__main__":
    hb = create_default_heartbeat()
    print("Running 3 heartbeats...")
    hb.run_loop(max_beats=3)
    print(f"Completed {hb.beat_count} beats")
