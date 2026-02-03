#!/usr/bin/env python3
"""
Threat Detector
===============
Detects interactions with known malicious addresses/programs on Solana.
Helps distinguish between "broken agent" and "agent attacked by malicious actor".

Inspired by BlockScoreBot's feedback on the forum.

SAFETY: Read-only, never signs transactions, never handles funds.
"""

import json
from dataclasses import dataclass
from typing import List, Set, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

import solana_rpc


class ThreatType(Enum):
    KNOWN_SCAM = "known_scam"
    RUGPULL = "rugpull"
    PHISHING = "phishing"
    DRAIN_ATTACK = "drain_attack"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"


@dataclass
class ThreatAssessment:
    """Assessment of an address or transaction."""
    address: str
    threat_type: ThreatType
    confidence: float  # 0.0 - 1.0
    reason: str
    source: str  # Where the threat intel came from
    timestamp: str


class ThreatDetector:
    """
    Detects known malicious addresses and suspicious patterns.
    
    Uses a local blacklist + pattern detection.
    Could be extended to integrate with external threat feeds.
    """
    
    def __init__(self, blacklist_file: str = "data/blacklist.json"):
        self.blacklist_file = Path(blacklist_file)
        self.blacklist: Set[str] = set()
        self.threat_patterns: List[Dict] = []
        self._load_blacklist()
        self._init_patterns()
    
    def _load_blacklist(self):
        """Load known malicious addresses."""
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file) as f:
                    data = json.load(f)
                    self.blacklist = set(data.get("addresses", []))
            except Exception:
                pass
        
        # Add some known patterns (example - would be updated with real data)
        # These are NOT real malicious addresses - just examples
        self.blacklist.update([
            # Placeholder - in production, this would be populated from threat feeds
        ])
    
    def _init_patterns(self):
        """Initialize suspicious pattern detectors."""
        self.threat_patterns = [
            {
                "name": "drain_signature",
                "description": "Multiple outbound transfers in rapid succession",
                "check": self._check_drain_pattern
            },
            {
                "name": "new_program_interaction",
                "description": "Interaction with very new/unverified program",
                "check": self._check_new_program
            }
        ]
    
    def _check_drain_pattern(self, address: str, tx_history: List[Dict]) -> Optional[ThreatAssessment]:
        """Check for drain attack patterns."""
        # Look for multiple outbound transfers in short time
        outbound_count = 0
        for tx in tx_history[:10]:
            if tx.get("err") is None:
                outbound_count += 1
        
        # If >5 successful txs in recent history, could be drain
        # This is a simplified heuristic
        if outbound_count > 5:
            return ThreatAssessment(
                address=address,
                threat_type=ThreatType.SUSPICIOUS,
                confidence=0.3,
                reason="High transaction frequency detected",
                source="pattern_analysis",
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
        return None
    
    def _check_new_program(self, program_id: str, account_info: Any) -> Optional[ThreatAssessment]:
        """Check if interacting with suspicious new program."""
        # In production, would check program age, verification status, etc.
        return None
    
    def check_address(self, address: str) -> ThreatAssessment:
        """Check if an address is known malicious or suspicious."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Check blacklist
        if address in self.blacklist:
            return ThreatAssessment(
                address=address,
                threat_type=ThreatType.KNOWN_SCAM,
                confidence=0.95,
                reason="Address is on known scam blacklist",
                source="local_blacklist",
                timestamp=timestamp
            )
        
        # Check transaction patterns
        tx_history = solana_rpc.get_signatures_for_address(address, limit=10)
        for pattern in self.threat_patterns:
            result = pattern["check"](address, tx_history)
            if result:
                return result
        
        # Clean
        return ThreatAssessment(
            address=address,
            threat_type=ThreatType.CLEAN,
            confidence=0.7,  # Can't be 100% sure
            reason="No threats detected",
            source="analysis",
            timestamp=timestamp
        )
    
    def add_to_blacklist(self, address: str, threat_type: ThreatType, reason: str):
        """Add an address to the local blacklist."""
        self.blacklist.add(address)
        
        # Save to file
        self.blacklist_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {"addresses": list(self.blacklist), "updated": datetime.utcnow().isoformat() + "Z"}
        
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file) as f:
                    existing = json.load(f)
                    data["history"] = existing.get("history", [])
            except:
                data["history"] = []
        else:
            data["history"] = []
        
        data["history"].append({
            "address": address,
            "threat_type": threat_type.value,
            "reason": reason,
            "added": datetime.utcnow().isoformat() + "Z"
        })
        
        with open(self.blacklist_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def analyze_incident(self, incident_evidence: Dict) -> Optional[ThreatAssessment]:
        """
        Analyze an incident to determine if it was caused by malicious actor.
        
        Helps distinguish:
        - "Agent broke due to bug" 
        - "Agent was attacked/scammed"
        """
        # Look for addresses in the evidence
        addresses_to_check = []
        
        # Extract any Solana addresses from evidence
        if "transactions" in incident_evidence:
            for tx in incident_evidence.get("transactions", {}).get("failures", []):
                sig = tx.get("signature")
                if sig:
                    # Get transaction details to find involved addresses
                    tx_result = solana_rpc.get_transaction(sig)
                    # Would extract addresses from tx_result.logs
        
        # Check each address
        for addr in addresses_to_check:
            assessment = self.check_address(addr)
            if assessment.threat_type != ThreatType.CLEAN:
                return assessment
        
        return None


# Global detector instance
threat_detector = ThreatDetector()


def check_address(address: str) -> ThreatAssessment:
    """Check if an address is malicious."""
    return threat_detector.check_address(address)


def analyze_incident_for_threats(evidence: Dict) -> Optional[ThreatAssessment]:
    """Analyze incident evidence for malicious actors."""
    return threat_detector.analyze_incident(evidence)


def blacklist_address(address: str, threat_type: ThreatType, reason: str):
    """Add address to blacklist."""
    threat_detector.add_to_blacklist(address, threat_type, reason)


if __name__ == "__main__":
    print("Threat Detector")
    print("-" * 40)
    
    # Test with system program (should be clean)
    test_addr = "11111111111111111111111111111111"
    result = check_address(test_addr)
    print(f"Address: {test_addr[:20]}...")
    print(f"Status: {result.threat_type.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Reason: {result.reason}")
