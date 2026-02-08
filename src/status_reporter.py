"""
AgentMedic Status Reporter
==========================
Generate status reports for external consumption.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any


class StatusReporter:
    """Generate status reports in various formats."""
    
    def __init__(self, agent_name: str = "AgentMedic"):
        self.agent_name = agent_name
        self.start_time = datetime.now(timezone.utc)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status as dict."""
        now = datetime.now(timezone.utc)
        uptime_seconds = (now - self.start_time).total_seconds()
        
        return {
            "agent": self.agent_name,
            "status": "healthy",
            "timestamp": now.isoformat(),
            "uptime_seconds": int(uptime_seconds),
            "version": "1.0.0",
            "modules": {
                "observer": True,
                "diagnoser": True,
                "recoverer": True,
                "verifier": True
            }
        }
    
    def to_json(self) -> str:
        """Get status as JSON string."""
        return json.dumps(self.get_status(), indent=2)
    
    def to_markdown(self) -> str:
        """Get status as markdown."""
        s = self.get_status()
        return f"""# {s['agent']} Status Report

**Status:** {s['status']}  
**Timestamp:** {s['timestamp']}  
**Uptime:** {s['uptime_seconds']}s  

## Modules
| Module | Status |
|--------|--------|
| Observer | {'✅' if s['modules']['observer'] else '❌'} |
| Diagnoser | {'✅' if s['modules']['diagnoser'] else '❌'} |
| Recoverer | {'✅' if s['modules']['recoverer'] else '❌'} |
| Verifier | {'✅' if s['modules']['verifier'] else '❌'} |
"""
    
    def to_oneline(self) -> str:
        """Get one-line status."""
        s = self.get_status()
        return f"[{s['agent']}] {s['status'].upper()} | uptime: {s['uptime_seconds']}s"


if __name__ == "__main__":
    reporter = StatusReporter()
    print(reporter.to_markdown())
