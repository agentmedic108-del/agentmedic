"""
AgentMedic Anomaly Detector
===========================
Detect anomalies in agent behavior and metrics.
"""

from dataclasses import dataclass
from typing import List, Optional
import statistics


@dataclass
class Anomaly:
    metric: str
    value: float
    expected: float
    deviation: float
    severity: str  # low, medium, high


class AnomalyDetector:
    """Statistical anomaly detection."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._history: dict = {}
    
    def record(self, metric: str, value: float):
        if metric not in self._history:
            self._history[metric] = []
        self._history[metric].append(value)
        if len(self._history[metric]) > self.window_size:
            self._history[metric] = self._history[metric][-self.window_size:]
    
    def detect(self, metric: str, value: float, threshold: float = 2.0) -> Optional[Anomaly]:
        history = self._history.get(metric, [])
        if len(history) < 10:
            return None
        
        mean = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 0
        
        if stdev == 0:
            return None
        
        z_score = abs(value - mean) / stdev
        
        if z_score < threshold:
            return None
        
        severity = "low"
        if z_score > 3:
            severity = "medium"
        if z_score > 4:
            severity = "high"
        
        return Anomaly(
            metric=metric,
            value=value,
            expected=mean,
            deviation=z_score,
            severity=severity
        )
    
    def check_all(self, metrics: dict) -> List[Anomaly]:
        anomalies = []
        for metric, value in metrics.items():
            self.record(metric, value)
            anomaly = self.detect(metric, value)
            if anomaly:
                anomalies.append(anomaly)
        return anomalies


_detector = None

def get_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector
