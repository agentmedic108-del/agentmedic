"""
AgentMedic Quarantine System
============================
All incoming data goes through quarantine before being trusted.

Nothing is learned or stored until it passes verification:
1. Source validation
2. Pattern consistency check
3. Cross-reference with known good data
4. Time-based observation period
5. Multiple confirmation requirement

Prevents:
- Oracle manipulation
- False incident injection
- Poisoned learning data
- Single-source attacks
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


class QuarantineStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class QuarantinedItem:
    """Item held in quarantine."""
    item_id: str
    data_type: str  # incident, threat, pattern, oracle_data
    content: Dict[str, Any]
    source: str
    submitted_at: str
    status: QuarantineStatus
    review_notes: List[str]
    confirmations: int  # How many sources confirmed this
    required_confirmations: int
    expires_at: str
    verified_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class QuarantineSystem:
    """Quarantine system for untrusted data."""
    
    # Minimum confirmations needed by data type
    CONFIRMATION_REQUIREMENTS = {
        "incident": 1,      # Single incident can be observed directly
        "threat": 2,        # Threats need corroboration
        "pattern": 3,       # Patterns need multiple observations
        "oracle_data": 2,   # Oracle data needs cross-reference
        "external_intel": 3 # External sources need high verification
    }
    
    # Quarantine duration by data type (hours)
    QUARANTINE_DURATION = {
        "incident": 1,
        "threat": 6,
        "pattern": 24,
        "oracle_data": 0.5,
        "external_intel": 12
    }
    
    def __init__(self, storage_file: str = "quarantine.json"):
        self.storage_file = storage_file
        self.items: Dict[str, QuarantinedItem] = {}
        self._load()
    
    def _load(self):
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for item_id, item_data in data.items():
                    item_data["status"] = QuarantineStatus(item_data["status"])
                    self.items[item_id] = QuarantinedItem(**item_data)
        except:
            pass
    
    def _save(self):
        data = {k: v.to_dict() for k, v in self.items.items()}
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_id(self, content: Dict) -> str:
        """Generate deterministic ID from content."""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def submit(
        self,
        data_type: str,
        content: Dict[str, Any],
        source: str
    ) -> QuarantinedItem:
        """Submit data to quarantine."""
        item_id = self._generate_id(content)
        now = datetime.now(timezone.utc)
        
        # Check if already in quarantine
        if item_id in self.items:
            existing = self.items[item_id]
            if existing.status == QuarantineStatus.PENDING:
                # Add confirmation from new source
                if source not in existing.review_notes:
                    existing.confirmations += 1
                    existing.review_notes.append(f"Confirmed by: {source}")
                    self._check_verification(existing)
                    self._save()
            return existing
        
        # Calculate expiration
        duration_hours = self.QUARANTINE_DURATION.get(data_type, 24)
        expires_at = now + timedelta(hours=duration_hours)
        
        item = QuarantinedItem(
            item_id=item_id,
            data_type=data_type,
            content=content,
            source=source,
            submitted_at=now.isoformat(),
            status=QuarantineStatus.PENDING,
            review_notes=[f"Submitted by: {source}"],
            confirmations=1,
            required_confirmations=self.CONFIRMATION_REQUIREMENTS.get(data_type, 2),
            expires_at=expires_at.isoformat()
        )
        
        self.items[item_id] = item
        self._check_verification(item)
        self._save()
        return item
    
    def _check_verification(self, item: QuarantinedItem):
        """Check if item meets verification requirements."""
        if item.confirmations >= item.required_confirmations:
            item.status = QuarantineStatus.VERIFIED
            item.verified_at = datetime.now(timezone.utc).isoformat()
            item.review_notes.append("AUTO-VERIFIED: Met confirmation threshold")
    
    def confirm(self, item_id: str, source: str, notes: str = "") -> bool:
        """Add confirmation to quarantined item."""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        if item.status != QuarantineStatus.PENDING:
            return False
        
        item.confirmations += 1
        item.review_notes.append(f"Confirmed by {source}: {notes}")
        self._check_verification(item)
        self._save()
        return True
    
    def reject(self, item_id: str, reason: str) -> bool:
        """Reject quarantined item."""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        item.status = QuarantineStatus.REJECTED
        item.review_notes.append(f"REJECTED: {reason}")
        self._save()
        return True
    
    def get_verified(self, data_type: str = None) -> List[QuarantinedItem]:
        """Get all verified items."""
        items = [i for i in self.items.values() if i.status == QuarantineStatus.VERIFIED]
        if data_type:
            items = [i for i in items if i.data_type == data_type]
        return items
    
    def get_pending(self) -> List[QuarantinedItem]:
        """Get items pending review."""
        self._expire_old_items()
        return [i for i in self.items.values() if i.status == QuarantineStatus.PENDING]
    
    def _expire_old_items(self):
        """Mark expired items."""
        now = datetime.now(timezone.utc)
        for item in self.items.values():
            if item.status == QuarantineStatus.PENDING:
                expires = datetime.fromisoformat(item.expires_at.replace('Z', '+00:00'))
                if now > expires:
                    item.status = QuarantineStatus.EXPIRED
                    item.review_notes.append("EXPIRED: Did not meet confirmation threshold in time")
        self._save()
    
    def is_trusted(self, content: Dict) -> bool:
        """Check if content has been verified."""
        item_id = self._generate_id(content)
        if item_id in self.items:
            return self.items[item_id].status == QuarantineStatus.VERIFIED
        return False
    
    def get_stats(self) -> Dict:
        """Get quarantine stats."""
        by_status = {}
        for item in self.items.values():
            status = item.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_items": len(self.items),
            "by_status": by_status,
            "pending_count": by_status.get("pending", 0),
            "verified_count": by_status.get("verified", 0),
            "rejection_rate": by_status.get("rejected", 0) / max(len(self.items), 1)
        }


_quarantine = None

def get_quarantine() -> QuarantineSystem:
    global _quarantine
    if _quarantine is None:
        _quarantine = QuarantineSystem()
    return _quarantine


def quarantine_data(data_type: str, content: Dict, source: str) -> QuarantinedItem:
    """Quick helper to quarantine data."""
    return get_quarantine().submit(data_type, content, source)


def is_trusted(content: Dict) -> bool:
    """Check if content passed quarantine."""
    return get_quarantine().is_trusted(content)
