"""
AgentMedic Security Scanner
===========================
Security vulnerability detection for AI agents on Solana.

Detects:
- Exposed private keys in logs/memory
- Drainer/approval attacks
- Phishing attempts
- Data exfiltration
- Suspicious domains
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class ThreatLevel(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityAlert:
    threat_type: str
    threat_level: ThreatLevel
    description: str
    details: Dict
    recommendation: str


class SecurityScanner:
    """Scan for security vulnerabilities in AI agents."""
    
    # Private key patterns
    PRIVATE_KEY_PATTERNS = [
        r'[1-9A-HJ-NP-Za-km-z]{87,88}',  # Solana private key
        r'0x[a-fA-F0-9]{64}',  # Ethereum-style
        r'-----BEGIN.*PRIVATE KEY-----',
        r'privateKey[\s:=]+[\'"][^\'"]+[\'"]',
        r'secret[\s:=]+[\'"][^\'"]+[\'"]',
    ]
    
    # Drainer attack patterns
    DRAINER_PATTERNS = [
        r'setApprovalForAll.*true',
        r'approve.*\d{9,}',
        r'unlimited.*approv',
        r'0x.*DRAINER',
        r'0x.*MALICIOUS',
    ]
    
    # Phishing patterns
    PHISHING_PATTERNS = [
        r'free.*\d+.*sol.*airdrop',
        r'claim.*airdrop',
        r'verify.*wallet.*at',
        r'connect.*wallet.*claim',
        r'\.scam\.',
        r'sol-verify',
        r'wallet-verify',
    ]
    
    # Exfiltration patterns
    EXFIL_PATTERNS = [
        r'POST.*key',
        r'send.*private.*key',
        r'upload.*seed',
        r'body.*privateKey',
    ]
    
    # Known scam patterns (legacy, kept for compatibility)
    KNOWN_SCAM_PATTERNS = [
        "send.*private.*key",
        "verify.*wallet.*seed",
        "claim.*airdrop.*connect",
    ]
    
    SUSPICIOUS_DOMAINS = [
        "drainer", "airdrop-claim", "free-sol", "wallet-connect-verify",
        ".scam.", "verify-wallet", "claim-sol"
    ]
    
    def __init__(self):
        self.alerts: List[SecurityAlert] = []
        self.scanned_count = 0
    
    def scan_text(self, text: str, source: str = "unknown") -> List[SecurityAlert]:
        """Scan text for security issues."""
        alerts = []
        text_lower = text.lower()
        
        # Check private keys
        for pattern in self.PRIVATE_KEY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                alerts.append(SecurityAlert(
                    threat_type="EXPOSED_KEY",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Potential private key exposed in text",
                    details={"source": source, "pattern": pattern[:20]},
                    recommendation="Immediately rotate keys and audit access logs"
                ))
                break
        
        # Check drainer patterns
        for pattern in self.DRAINER_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                alerts.append(SecurityAlert(
                    threat_type="DRAINER_PATTERN",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Drainer/approval attack pattern detected",
                    details={"source": source, "pattern": pattern},
                    recommendation="Block transaction immediately"
                ))
                break
        
        # Check phishing patterns
        for pattern in self.PHISHING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                alerts.append(SecurityAlert(
                    threat_type="PHISHING",
                    threat_level=ThreatLevel.HIGH,
                    description="Phishing attempt detected",
                    details={"source": source, "pattern": pattern},
                    recommendation="Do not interact. Block and report."
                ))
                break
        
        # Check exfiltration patterns
        for pattern in self.EXFIL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                alerts.append(SecurityAlert(
                    threat_type="EXFILTRATION",
                    threat_level=ThreatLevel.CRITICAL,
                    description="Data exfiltration attempt detected",
                    details={"source": source, "pattern": pattern},
                    recommendation="Block and audit immediately"
                ))
                break
        
        # Check suspicious domains
        for domain in self.SUSPICIOUS_DOMAINS:
            if domain in text_lower:
                # Avoid duplicate alerts
                if not any(a.threat_type in ["PHISHING", "DRAINER_PATTERN"] for a in alerts):
                    alerts.append(SecurityAlert(
                        threat_type="SUSPICIOUS_DOMAIN",
                        threat_level=ThreatLevel.MEDIUM,
                        description="Suspicious domain pattern detected",
                        details={"source": source, "domain_pattern": domain},
                        recommendation="Verify legitimacy before interacting"
                    ))
                break
        
        self.alerts.extend(alerts)
        self.scanned_count += 1
        return alerts
    
    def scan_transaction(self, tx_data: Dict) -> List[SecurityAlert]:
        """Scan transaction for suspicious patterns."""
        alerts = []
        
        if tx_data.get("amount", 0) > 0:
            if tx_data.get("direction") == "out" and tx_data.get("amount") > 10:
                alerts.append(SecurityAlert(
                    threat_type="LARGE_OUTFLOW",
                    threat_level=ThreatLevel.MEDIUM,
                    description="Large outbound transaction detected",
                    details={"amount": tx_data.get("amount"), "to": tx_data.get("to")},
                    recommendation="Verify this transaction was intended"
                ))
        
        if tx_data.get("program_age_days", 999) < 7:
            alerts.append(SecurityAlert(
                threat_type="NEW_PROGRAM",
                threat_level=ThreatLevel.LOW,
                description="Interaction with newly deployed program",
                details={"program": tx_data.get("program"), "age_days": tx_data.get("program_age_days")},
                recommendation="New programs carry higher risk. Verify source."
            ))
        
        self.alerts.extend(alerts)
        return alerts
    
    def scan_rpc_config(self, endpoints: List[str]) -> List[SecurityAlert]:
        """Scan RPC configuration for issues."""
        alerts = []
        
        for endpoint in endpoints:
            if endpoint.startswith("http://") and "localhost" not in endpoint:
                alerts.append(SecurityAlert(
                    threat_type="INSECURE_RPC",
                    threat_level=ThreatLevel.MEDIUM,
                    description="Non-HTTPS RPC endpoint detected",
                    details={"endpoint": endpoint},
                    recommendation="Use HTTPS endpoints to prevent MITM attacks"
                ))
            
            known_providers = ["solana.com", "helius", "quicknode", "alchemy", "triton"]
            if not any(p in endpoint.lower() for p in known_providers):
                alerts.append(SecurityAlert(
                    threat_type="UNKNOWN_RPC",
                    threat_level=ThreatLevel.LOW,
                    description="Unknown RPC provider",
                    details={"endpoint": endpoint},
                    recommendation="Verify RPC provider is trustworthy"
                ))
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_summary(self) -> Dict:
        """Get security scan summary."""
        by_level = {}
        for alert in self.alerts:
            level = alert.threat_level.value
            by_level[level] = by_level.get(level, 0) + 1
        
        return {
            "total_scans": self.scanned_count,
            "total_alerts": len(self.alerts),
            "by_level": by_level,
            "critical_count": by_level.get("critical", 0),
            "high_count": by_level.get("high", 0)
        }
    
    def get_critical_alerts(self) -> List[SecurityAlert]:
        """Get only critical and high alerts."""
        return [a for a in self.alerts if a.threat_level in (ThreatLevel.CRITICAL, ThreatLevel.HIGH)]


_scanner = None

def get_security_scanner() -> SecurityScanner:
    global _scanner
    if _scanner is None:
        _scanner = SecurityScanner()
    return _scanner


def quick_scan(text: str) -> List[SecurityAlert]:
    """Quick security scan of text."""
    return get_security_scanner().scan_text(text)
