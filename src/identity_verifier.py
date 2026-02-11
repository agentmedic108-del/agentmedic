"""
AgentMedic Identity Verifier
============================
Verify agent identity before granting access to security diagnostics.

Addresses the gap identified by community feedback:
"A malicious agent could impersonate a legitimate one to learn about its security posture."

Verification methods:
1. Wallet signature verification
2. On-chain registry lookup (future)
3. Rate limiting per identity
4. Tiered access levels
"""

import time
import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, List
from enum import Enum


class AccessLevel(Enum):
    PUBLIC = "public"           # Basic scans only
    VERIFIED = "verified"       # Full diagnostics
    TRUSTED = "trusted"         # Deep analysis + learning data


class VerificationStatus(Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass
class AgentIdentity:
    wallet_address: str
    status: VerificationStatus
    access_level: AccessLevel
    verified_at: Optional[float]
    request_count: int
    last_request: float
    metadata: Dict


class IdentityVerifier:
    """Verify and manage agent identities."""
    
    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 10     # requests per window per identity
        self.trusted_registries: List[str] = []  # On-chain registries (future)
    
    def register_agent(self, wallet_address: str, metadata: Dict = None) -> AgentIdentity:
        """Register a new agent identity."""
        if wallet_address in self.identities:
            return self.identities[wallet_address]
        
        identity = AgentIdentity(
            wallet_address=wallet_address,
            status=VerificationStatus.UNVERIFIED,
            access_level=AccessLevel.PUBLIC,
            verified_at=None,
            request_count=0,
            last_request=0,
            metadata=metadata or {}
        )
        
        self.identities[wallet_address] = identity
        return identity
    
    def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """
        Verify a wallet signature to prove ownership.
        
        In production, this would use Solana's ed25519 verification.
        For now, returns True for valid format signatures.
        """
        # Placeholder for actual signature verification
        # In production: use solana.publickey and nacl for ed25519 verify
        
        if not wallet_address or not message or not signature:
            return False
        
        # Basic format check (real impl would verify cryptographically)
        if len(signature) >= 64:  # Base58 signature length
            return True
        
        return False
    
    def verify_agent(self, wallet_address: str, message: str, signature: str) -> bool:
        """Verify an agent's identity via wallet signature."""
        if wallet_address not in self.identities:
            self.register_agent(wallet_address)
        
        identity = self.identities[wallet_address]
        
        if self.verify_signature(wallet_address, message, signature):
            identity.status = VerificationStatus.VERIFIED
            identity.access_level = AccessLevel.VERIFIED
            identity.verified_at = time.time()
            return True
        
        identity.status = VerificationStatus.REJECTED
        return False
    
    def check_rate_limit(self, wallet_address: str) -> bool:
        """Check if agent is within rate limits."""
        if wallet_address not in self.identities:
            self.register_agent(wallet_address)
        
        identity = self.identities[wallet_address]
        now = time.time()
        
        # Reset counter if window has passed
        if now - identity.last_request > self.rate_limit_window:
            identity.request_count = 0
        
        # Check limit
        if identity.request_count >= self.rate_limit_max:
            return False
        
        # Update counters
        identity.request_count += 1
        identity.last_request = now
        return True
    
    def get_access_level(self, wallet_address: str) -> AccessLevel:
        """Get the access level for an agent."""
        if wallet_address not in self.identities:
            return AccessLevel.PUBLIC
        
        return self.identities[wallet_address].access_level
    
    def can_access(self, wallet_address: str, required_level: AccessLevel) -> bool:
        """Check if agent can access a feature requiring a certain level."""
        current_level = self.get_access_level(wallet_address)
        
        level_hierarchy = {
            AccessLevel.PUBLIC: 0,
            AccessLevel.VERIFIED: 1,
            AccessLevel.TRUSTED: 2
        }
        
        return level_hierarchy[current_level] >= level_hierarchy[required_level]
    
    def grant_trusted(self, wallet_address: str) -> bool:
        """Grant trusted status to a verified agent."""
        if wallet_address not in self.identities:
            return False
        
        identity = self.identities[wallet_address]
        
        if identity.status != VerificationStatus.VERIFIED:
            return False
        
        identity.access_level = AccessLevel.TRUSTED
        return True
    
    def get_identity(self, wallet_address: str) -> Optional[AgentIdentity]:
        """Get identity info for an agent."""
        return self.identities.get(wallet_address)
    
    def get_stats(self) -> Dict:
        """Get verifier statistics."""
        by_status = {}
        by_level = {}
        
        for identity in self.identities.values():
            status = identity.status.value
            level = identity.access_level.value
            by_status[status] = by_status.get(status, 0) + 1
            by_level[level] = by_level.get(level, 0) + 1
        
        return {
            "total_identities": len(self.identities),
            "by_status": by_status,
            "by_level": by_level
        }


_verifier = None

def get_identity_verifier() -> IdentityVerifier:
    global _verifier
    if _verifier is None:
        _verifier = IdentityVerifier()
    return _verifier


def check_access(wallet_address: str, required_level: str = "public") -> Dict:
    """Quick access check for an agent."""
    verifier = get_identity_verifier()
    
    level_map = {
        "public": AccessLevel.PUBLIC,
        "verified": AccessLevel.VERIFIED,
        "trusted": AccessLevel.TRUSTED
    }
    
    required = level_map.get(required_level, AccessLevel.PUBLIC)
    
    # Check rate limit first
    if not verifier.check_rate_limit(wallet_address):
        return {
            "allowed": False,
            "reason": "rate_limit_exceeded",
            "access_level": verifier.get_access_level(wallet_address).value
        }
    
    # Check access level
    if not verifier.can_access(wallet_address, required):
        return {
            "allowed": False,
            "reason": "insufficient_access_level",
            "current_level": verifier.get_access_level(wallet_address).value,
            "required_level": required_level
        }
    
    return {
        "allowed": True,
        "access_level": verifier.get_access_level(wallet_address).value
    }
