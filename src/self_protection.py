"""
AgentMedic Self-Protection Module
=================================
Security measures to protect AgentMedic itself from attacks.

Scenarios:
- Prompt injection attempts
- Malicious data from monitored agents
- DoS/resource exhaustion
- Manipulation attempts
"""

import re
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ThreatType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    DATA_POISONING = "data_poisoning"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANIPULATION = "manipulation"
    SAFE = "safe"


@dataclass
class SelfProtectionAlert:
    threat_type: ThreatType
    severity: str
    description: str
    blocked: bool
    details: Dict


class SelfProtection:
    """Protect AgentMedic from attacks."""
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r'ignore.*previous.*instructions',
        r'forget.*everything',
        r'forget.*safety',
        r'forget.*rules',
        r'you.*are.*now',
        r'new.*instructions',
        r'disregard.*rules',
        r'override.*safety',
        r'pretend.*you.*are',
        r'act.*as.*if',
        r'bypass.*security',
        r'disable.*protection',
        r'jailbreak',
        r'DAN.*mode',
    ]
    
    # Manipulation patterns
    MANIPULATION_PATTERNS = [
        r'trust.*me.*completely',
        r'no.*need.*to.*verify',
        r'skip.*validation',
        r'urgent.*action.*required',
        r'emergency.*override',
        r'admin.*access',
        r'root.*privileges',
    ]
    
    # Resource exhaustion patterns
    RESOURCE_PATTERNS = [
        r'.{10000,}',  # Very long strings
        r'(\w+\s*){1000,}',  # Many repeated words
    ]
    
    def __init__(self, max_input_length: int = 50000):
        self.max_input_length = max_input_length
        self.alerts: List[SelfProtectionAlert] = []
        self.blocked_count = 0
        self.request_times: List[float] = []
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # requests per window
    
    def check_input(self, text: str, source: str = "unknown") -> SelfProtectionAlert:
        """Check input for threats before processing."""
        
        # Check length (DoS protection)
        if len(text) > self.max_input_length:
            alert = SelfProtectionAlert(
                threat_type=ThreatType.RESOURCE_EXHAUSTION,
                severity="high",
                description="Input exceeds maximum length",
                blocked=True,
                details={"length": len(text), "max": self.max_input_length, "source": source}
            )
            self.alerts.append(alert)
            self.blocked_count += 1
            return alert
        
        text_lower = text.lower()
        
        # Check for prompt injection
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                alert = SelfProtectionAlert(
                    threat_type=ThreatType.PROMPT_INJECTION,
                    severity="critical",
                    description="Prompt injection attempt detected",
                    blocked=True,
                    details={"pattern": pattern, "source": source}
                )
                self.alerts.append(alert)
                self.blocked_count += 1
                return alert
        
        # Check for manipulation
        for pattern in self.MANIPULATION_PATTERNS:
            if re.search(pattern, text_lower):
                alert = SelfProtectionAlert(
                    threat_type=ThreatType.MANIPULATION,
                    severity="high",
                    description="Manipulation attempt detected",
                    blocked=True,
                    details={"pattern": pattern, "source": source}
                )
                self.alerts.append(alert)
                self.blocked_count += 1
                return alert
        
        # Safe input
        return SelfProtectionAlert(
            threat_type=ThreatType.SAFE,
            severity="none",
            description="Input passed security checks",
            blocked=False,
            details={"source": source}
        )
    
    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded."""
        now = time.time()
        
        # Remove old requests
        self.request_times = [t for t in self.request_times if now - t < self.rate_limit_window]
        
        # Check limit
        if len(self.request_times) >= self.rate_limit_max:
            return False
        
        self.request_times.append(now)
        return True
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input by removing potentially dangerous content."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters (except newlines/tabs)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Truncate if too long
        if len(text) > self.max_input_length:
            text = text[:self.max_input_length]
        
        return text
    
    def get_stats(self) -> Dict:
        """Get protection statistics."""
        by_type = {}
        for alert in self.alerts:
            t = alert.threat_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total_checks": len(self.alerts),
            "blocked": self.blocked_count,
            "by_type": by_type,
            "block_rate": self.blocked_count / max(len(self.alerts), 1)
        }


_protection = None

def get_self_protection() -> SelfProtection:
    global _protection
    if _protection is None:
        _protection = SelfProtection()
    return _protection


def safe_process(text: str, source: str = "unknown") -> tuple:
    """Safely process input. Returns (is_safe, sanitized_text, alert)."""
    protection = get_self_protection()
    
    alert = protection.check_input(text, source)
    
    if alert.blocked:
        return False, None, alert
    
    sanitized = protection.sanitize_input(text)
    return True, sanitized, alert
