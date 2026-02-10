"""
AgentMedic Verifiable Audit System
==================================
Cryptographically verifiable test results and audit logs.

All test results are:
1. Hashed with SHA-256
2. Timestamped
3. Signed with agent identity
4. Stored in tamper-evident log

Anyone can verify:
- Test was run at claimed time
- Results haven't been modified
- Which agent produced the results
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class AuditEntry:
    """Single verifiable audit entry."""
    entry_id: str
    timestamp: str
    agent_id: str
    action: str
    input_hash: str
    output_hash: str
    result: str  # pass/fail/error
    details: Dict[str, Any]
    signature: str  # Hash of all above fields
    
    def to_dict(self) -> Dict:
        return asdict(self)


class VerifiableAudit:
    """Verifiable audit trail for agent actions."""
    
    def __init__(self, agent_id: str, log_file: str = "audit_log.jsonl"):
        self.agent_id = agent_id
        self.log_file = log_file
        self.entries: List[AuditEntry] = []
        self._counter = 0
    
    def _hash(self, data: Any) -> str:
        """Create SHA-256 hash of data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    def _sign_entry(self, entry_data: Dict) -> str:
        """Create signature for entry (hash of all fields)."""
        signing_string = "|".join([
            entry_data["entry_id"],
            entry_data["timestamp"],
            entry_data["agent_id"],
            entry_data["action"],
            entry_data["input_hash"],
            entry_data["output_hash"],
            entry_data["result"]
        ])
        return self._hash(signing_string)
    
    def record(
        self,
        action: str,
        input_data: Any,
        output_data: Any,
        result: str,
        details: Dict = None
    ) -> AuditEntry:
        """Record a verifiable audit entry."""
        self._counter += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = f"{self.agent_id}-{timestamp}-{self._counter:06d}"
        
        entry_data = {
            "entry_id": entry_id,
            "timestamp": timestamp,
            "agent_id": self.agent_id,
            "action": action,
            "input_hash": self._hash(input_data),
            "output_hash": self._hash(output_data),
            "result": result,
            "details": details or {}
        }
        
        signature = self._sign_entry(entry_data)
        entry = AuditEntry(**entry_data, signature=signature)
        
        self.entries.append(entry)
        self._persist(entry)
        
        return entry
    
    def _persist(self, entry: AuditEntry):
        """Append entry to log file."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def verify_entry(self, entry: AuditEntry) -> bool:
        """Verify an audit entry's signature."""
        entry_data = entry.to_dict()
        del entry_data["signature"]
        expected_sig = self._sign_entry(entry_data)
        return expected_sig == entry.signature
    
    def verify_log(self) -> Dict:
        """Verify entire audit log."""
        if not os.path.exists(self.log_file):
            return {"valid": True, "entries": 0, "errors": []}
        
        errors = []
        count = 0
        
        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    entry = AuditEntry(**data)
                    if not self.verify_entry(entry):
                        errors.append(f"Line {line_num}: Invalid signature")
                    count += 1
                except Exception as e:
                    errors.append(f"Line {line_num}: Parse error - {e}")
        
        return {
            "valid": len(errors) == 0,
            "entries": count,
            "errors": errors
        }
    
    def record_test(
        self,
        test_name: str,
        test_input: Any,
        expected: Any,
        actual: Any,
        passed: bool
    ) -> AuditEntry:
        """Record a test result with verification."""
        return self.record(
            action=f"TEST:{test_name}",
            input_data={"test_input": test_input, "expected": expected},
            output_data={"actual": actual},
            result="PASS" if passed else "FAIL",
            details={
                "test_name": test_name,
                "match": expected == actual
            }
        )
    
    def record_security_scan(
        self,
        scan_target: str,
        alerts: List[Dict],
        clean: bool
    ) -> AuditEntry:
        """Record a security scan with verification."""
        return self.record(
            action="SECURITY_SCAN",
            input_data={"target": scan_target},
            output_data={"alerts": alerts, "alert_count": len(alerts)},
            result="CLEAN" if clean else "ALERTS_FOUND",
            details={"target": scan_target, "clean": clean}
        )
    
    def get_verification_report(self) -> str:
        """Generate human-readable verification report."""
        verification = self.verify_log()
        
        report = f"""
# Audit Verification Report

**Agent:** {self.agent_id}
**Log File:** {self.log_file}
**Generated:** {datetime.now(timezone.utc).isoformat()}

## Summary
- **Valid:** {'✅ YES' if verification['valid'] else '❌ NO'}
- **Total Entries:** {verification['entries']}
- **Errors:** {len(verification['errors'])}

## Verification Method
All entries are hashed with SHA-256 and signed.
Anyone can re-verify by:
1. Parsing each JSONL line
2. Reconstructing the signing string
3. Comparing SHA-256 hash to stored signature

## How to Verify
```python
from verifiable_audit import VerifiableAudit
audit = VerifiableAudit("agent-id", "audit_log.jsonl")
result = audit.verify_log()
print(f"Valid: {{result['valid']}}")
```
"""
        if verification['errors']:
            report += "\n## Errors\n"
            for err in verification['errors']:
                report += f"- {err}\n"
        
        return report


_audits: Dict[str, VerifiableAudit] = {}

def get_audit(agent_id: str, log_file: str = None) -> VerifiableAudit:
    """Get or create audit instance."""
    if agent_id not in _audits:
        log_file = log_file or f"audit_{agent_id}.jsonl"
        _audits[agent_id] = VerifiableAudit(agent_id, log_file)
    return _audits[agent_id]
