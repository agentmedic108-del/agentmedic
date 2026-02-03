"""
Pattern Analyzer
================
Analyzes historical incidents to detect recurring patterns.
Enables predictive/preemptive recovery actions.

Inspired by forum feedback from @moltdev on diagnostic memory.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


@dataclass
class Pattern:
    """Detected incident pattern."""
    pattern_id: str
    pattern_type: str  # temporal, frequency, correlation
    description: str
    confidence: float  # 0.0 - 1.0
    occurrences: int
    last_seen: str
    affected_agents: List[str]
    mitigation: str


class PatternAnalyzer:
    """Analyzes incident history to detect patterns."""
    
    def __init__(self, incident_file: str = "logs/incident_report.json"):
        self.incident_file = Path(incident_file)
        self.patterns: List[Pattern] = []
    
    def load_incidents(self) -> List[Dict]:
        """Load incident history."""
        if not self.incident_file.exists():
            return []
        
        try:
            with open(self.incident_file) as f:
                data = json.load(f)
                return data.get("incidents", [])
        except Exception:
            return []
    
    def analyze_temporal_patterns(self, incidents: List[Dict]) -> List[Pattern]:
        """Detect time-based patterns (e.g., failures at specific hours)."""
        patterns = []
        
        # Group incidents by hour of day
        hour_counts = defaultdict(list)
        for inc in incidents:
            try:
                ts = datetime.fromisoformat(inc["timestamp"].replace("Z", "+00:00"))
                hour_counts[ts.hour].append(inc)
            except Exception:
                continue
        
        # Detect hours with high incident rates
        total = len(incidents)
        if total < 5:
            return patterns  # Not enough data
        
        for hour, hour_incidents in hour_counts.items():
            rate = len(hour_incidents) / total
            if rate > 0.3 and len(hour_incidents) >= 3:  # 30%+ of incidents in one hour
                patterns.append(Pattern(
                    pattern_id=f"TEMPORAL-HOUR-{hour:02d}",
                    pattern_type="temporal",
                    description=f"High incident rate at {hour:02d}:00 UTC ({len(hour_incidents)} incidents, {rate*100:.0f}%)",
                    confidence=min(rate * 1.5, 0.95),
                    occurrences=len(hour_incidents),
                    last_seen=max(i["timestamp"] for i in hour_incidents),
                    affected_agents=list(set(i.get("agent", "unknown") for i in hour_incidents)),
                    mitigation=f"Consider preemptive restart or health check at {(hour-1)%24:02d}:45 UTC"
                ))
        
        return patterns
    
    def analyze_frequency_patterns(self, incidents: List[Dict]) -> List[Pattern]:
        """Detect agents with frequent failures."""
        patterns = []
        
        # Group by agent and type
        agent_type_counts = defaultdict(lambda: defaultdict(list))
        for inc in incidents:
            agent = inc.get("agent", "unknown")
            inc_type = inc.get("type", "unknown")
            agent_type_counts[agent][inc_type].append(inc)
        
        for agent, type_counts in agent_type_counts.items():
            for inc_type, type_incidents in type_counts.items():
                if len(type_incidents) >= 3:
                    patterns.append(Pattern(
                        pattern_id=f"FREQ-{agent}-{inc_type}".upper(),
                        pattern_type="frequency",
                        description=f"Agent '{agent}' has recurring {inc_type} failures ({len(type_incidents)} times)",
                        confidence=min(0.5 + (len(type_incidents) * 0.1), 0.95),
                        occurrences=len(type_incidents),
                        last_seen=max(i["timestamp"] for i in type_incidents),
                        affected_agents=[agent],
                        mitigation=f"Investigate root cause of {inc_type} for '{agent}'. Consider configuration changes."
                    ))
        
        return patterns
    
    def analyze_correlation_patterns(self, incidents: List[Dict]) -> List[Pattern]:
        """Detect correlated failures (e.g., RPC down causes multiple agent failures)."""
        patterns = []
        
        # Group incidents by timestamp proximity (within 5 minutes)
        sorted_incidents = sorted(incidents, key=lambda x: x.get("timestamp", ""))
        
        clusters = []
        current_cluster = []
        
        for inc in sorted_incidents:
            try:
                ts = datetime.fromisoformat(inc["timestamp"].replace("Z", "+00:00"))
                
                if not current_cluster:
                    current_cluster = [inc]
                else:
                    last_ts = datetime.fromisoformat(
                        current_cluster[-1]["timestamp"].replace("Z", "+00:00")
                    )
                    if (ts - last_ts) <= timedelta(minutes=5):
                        current_cluster.append(inc)
                    else:
                        if len(current_cluster) >= 2:
                            clusters.append(current_cluster)
                        current_cluster = [inc]
            except Exception:
                continue
        
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        # Analyze clusters for correlation
        for cluster in clusters:
            if len(cluster) >= 2:
                agents = list(set(i.get("agent", "unknown") for i in cluster))
                types = list(set(i.get("type", "unknown") for i in cluster))
                
                # Check if RPC-related
                has_rpc = any("rpc" in t.lower() for t in types)
                
                if has_rpc and len(agents) > 1:
                    patterns.append(Pattern(
                        pattern_id=f"CORR-RPC-CASCADE-{len(patterns)+1}",
                        pattern_type="correlation",
                        description=f"RPC issues caused cascading failures across {len(agents)} agents",
                        confidence=0.8,
                        occurrences=len(cluster),
                        last_seen=cluster[-1]["timestamp"],
                        affected_agents=agents,
                        mitigation="Implement RPC failover and increase health check frequency during RPC issues"
                    ))
                elif len(agents) > 1:
                    patterns.append(Pattern(
                        pattern_id=f"CORR-MULTI-{len(patterns)+1}",
                        pattern_type="correlation",
                        description=f"Multiple agents failed within 5 minutes ({len(agents)} agents)",
                        confidence=0.6,
                        occurrences=len(cluster),
                        last_seen=cluster[-1]["timestamp"],
                        affected_agents=agents,
                        mitigation="Investigate shared dependencies or infrastructure issues"
                    ))
        
        return patterns
    
    def analyze(self) -> List[Pattern]:
        """Run all pattern analyses."""
        incidents = self.load_incidents()
        
        if not incidents:
            return []
        
        patterns = []
        patterns.extend(self.analyze_temporal_patterns(incidents))
        patterns.extend(self.analyze_frequency_patterns(incidents))
        patterns.extend(self.analyze_correlation_patterns(incidents))
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        self.patterns = patterns
        return patterns
    
    def get_preemptive_actions(self) -> List[Dict[str, Any]]:
        """Get recommended preemptive actions based on patterns."""
        actions = []
        
        for pattern in self.patterns:
            if pattern.confidence >= 0.7:
                actions.append({
                    "pattern_id": pattern.pattern_id,
                    "action": pattern.mitigation,
                    "confidence": pattern.confidence,
                    "affected_agents": pattern.affected_agents
                })
        
        return actions


# Global analyzer
analyzer = PatternAnalyzer()

def analyze_patterns() -> List[Pattern]:
    """Convenience function to run analysis."""
    return analyzer.analyze()

def get_recommendations() -> List[Dict[str, Any]]:
    """Get preemptive action recommendations."""
    analyzer.analyze()
    return analyzer.get_preemptive_actions()


if __name__ == "__main__":
    print("Pattern Analyzer")
    print("-" * 40)
    
    patterns = analyze_patterns()
    
    if not patterns:
        print("No patterns detected (need more incident history)")
    else:
        print(f"Detected {len(patterns)} patterns:\n")
        for p in patterns:
            print(f"[{p.confidence*100:.0f}%] {p.pattern_id}")
            print(f"     {p.description}")
            print(f"     Mitigation: {p.mitigation}")
            print()
