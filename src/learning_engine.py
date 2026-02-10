"""
AgentMedic Learning Engine
==========================
Self-learning system that improves from every incident.

Learns from:
- Agent failures and their root causes
- Successful recoveries and what worked
- New threat patterns discovered
- Community-shared threat intelligence
"""

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from collections import defaultdict


@dataclass
class LearnedPattern:
    """A pattern learned from experience."""
    pattern_id: str
    category: str  # failure, threat, recovery
    signature: str  # How to detect this
    description: str
    first_seen: str
    times_seen: int
    success_rate: float  # For recovery patterns
    source: str  # Where we learned this


class LearningEngine:
    """Self-learning engine for AgentMedic."""
    
    def __init__(self, knowledge_file: str = "learned_knowledge.json"):
        self.knowledge_file = knowledge_file
        self.patterns: Dict[str, LearnedPattern] = {}
        self.incident_history: List[Dict] = []
        self.threat_signatures: List[str] = []
        self._load()
    
    def _load(self):
        """Load existing knowledge."""
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r') as f:
                    data = json.load(f)
                    for pid, pdata in data.get("patterns", {}).items():
                        self.patterns[pid] = LearnedPattern(**pdata)
                    self.threat_signatures = data.get("threat_signatures", [])
            except:
                pass
    
    def _save(self):
        """Persist knowledge."""
        data = {
            "patterns": {pid: asdict(p) for pid, p in self.patterns.items()},
            "threat_signatures": self.threat_signatures,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.knowledge_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def learn_from_incident(
        self,
        incident_type: str,
        root_cause: str,
        symptoms: List[str],
        recovery_action: str,
        success: bool
    ):
        """Learn from an incident."""
        pattern_id = f"incident_{incident_type}_{len(self.patterns)}"
        
        # Check if similar pattern exists
        for pid, pattern in self.patterns.items():
            if pattern.category == "failure" and incident_type in pattern.signature:
                pattern.times_seen += 1
                if success:
                    pattern.success_rate = (pattern.success_rate + 1) / 2
                self._save()
                return pattern
        
        # New pattern
        pattern = LearnedPattern(
            pattern_id=pattern_id,
            category="failure",
            signature=f"{incident_type}|{root_cause}",
            description=f"Incident: {incident_type}, Cause: {root_cause}",
            first_seen=datetime.now(timezone.utc).isoformat(),
            times_seen=1,
            success_rate=1.0 if success else 0.0,
            source="incident_learning"
        )
        
        self.patterns[pattern_id] = pattern
        self._save()
        return pattern
    
    def learn_threat(
        self,
        threat_type: str,
        signature: str,
        description: str,
        source: str = "detection"
    ):
        """Learn a new threat pattern."""
        if signature in self.threat_signatures:
            return None
        
        pattern_id = f"threat_{len(self.patterns)}"
        pattern = LearnedPattern(
            pattern_id=pattern_id,
            category="threat",
            signature=signature,
            description=description,
            first_seen=datetime.now(timezone.utc).isoformat(),
            times_seen=1,
            success_rate=0.0,
            source=source
        )
        
        self.patterns[pattern_id] = pattern
        self.threat_signatures.append(signature)
        self._save()
        return pattern
    
    def learn_recovery(
        self,
        failure_type: str,
        recovery_action: str,
        success: bool
    ):
        """Learn which recovery actions work."""
        pattern_id = f"recovery_{failure_type}"
        
        if pattern_id in self.patterns:
            p = self.patterns[pattern_id]
            p.times_seen += 1
            # Update success rate with exponential moving average
            p.success_rate = 0.7 * p.success_rate + 0.3 * (1.0 if success else 0.0)
        else:
            self.patterns[pattern_id] = LearnedPattern(
                pattern_id=pattern_id,
                category="recovery",
                signature=f"{failure_type}|{recovery_action}",
                description=f"Recovery for {failure_type}: {recovery_action}",
                first_seen=datetime.now(timezone.utc).isoformat(),
                times_seen=1,
                success_rate=1.0 if success else 0.0,
                source="recovery_learning"
            )
        
        self._save()
        return self.patterns[pattern_id]
    
    def get_best_recovery(self, failure_type: str) -> Optional[str]:
        """Get best known recovery for a failure type."""
        best = None
        best_score = 0
        
        for pattern in self.patterns.values():
            if pattern.category == "recovery" and failure_type in pattern.signature:
                score = pattern.success_rate * min(pattern.times_seen, 10) / 10
                if score > best_score:
                    best_score = score
                    best = pattern.signature.split("|")[1] if "|" in pattern.signature else None
        
        return best
    
    def get_known_threats(self) -> List[str]:
        """Get all known threat signatures."""
        return self.threat_signatures.copy()
    
    def get_stats(self) -> Dict:
        """Get learning stats."""
        by_category = defaultdict(int)
        for p in self.patterns.values():
            by_category[p.category] += 1
        
        return {
            "total_patterns": len(self.patterns),
            "by_category": dict(by_category),
            "threat_signatures": len(self.threat_signatures),
            "avg_success_rate": sum(p.success_rate for p in self.patterns.values()) / max(len(self.patterns), 1)
        }


_engine = None

def get_learning_engine() -> LearningEngine:
    global _engine
    if _engine is None:
        _engine = LearningEngine()
    return _engine
