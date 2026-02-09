"""
AgentMedic Health Score Calculator
==================================
Calculate overall health scores for monitored agents.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class HealthGrade(Enum):
    A = "Excellent"
    B = "Good"
    C = "Fair"
    D = "Poor"
    F = "Critical"


@dataclass
class HealthScore:
    score: float  # 0-100
    grade: HealthGrade
    factors: Dict[str, float]
    recommendations: List[str]
    
    @property
    def emoji(self) -> str:
        return {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}[self.grade.name]


class HealthScoreCalculator:
    """Calculate health scores based on multiple factors."""
    
    WEIGHTS = {
        "uptime": 0.30,
        "response_time": 0.20,
        "error_rate": 0.25,
        "recovery_rate": 0.15,
        "resource_usage": 0.10
    }
    
    def calculate(
        self,
        uptime_pct: float = 100,
        avg_response_ms: float = 100,
        error_rate_pct: float = 0,
        recovery_rate_pct: float = 100,
        cpu_pct: float = 50,
        memory_pct: float = 50
    ) -> HealthScore:
        """Calculate overall health score."""
        
        factors = {}
        recommendations = []
        
        # Uptime score (100% = 100 points)
        factors["uptime"] = min(100, uptime_pct)
        if uptime_pct < 99:
            recommendations.append("Improve uptime - consider redundancy")
        
        # Response time (0-100ms = 100 points, >1000ms = 0)
        factors["response_time"] = max(0, 100 - (avg_response_ms / 10))
        if avg_response_ms > 500:
            recommendations.append("High latency - check RPC endpoints")
        
        # Error rate (0% = 100 points, >10% = 0)
        factors["error_rate"] = max(0, 100 - (error_rate_pct * 10))
        if error_rate_pct > 5:
            recommendations.append("High error rate - review logs")
        
        # Recovery rate
        factors["recovery_rate"] = min(100, recovery_rate_pct)
        if recovery_rate_pct < 90:
            recommendations.append("Recovery failures - check recovery procedures")
        
        # Resource usage (50% = optimal, penalty for >80%)
        resource_score = 100
        if cpu_pct > 80:
            resource_score -= (cpu_pct - 80) * 2
            recommendations.append("High CPU usage")
        if memory_pct > 80:
            resource_score -= (memory_pct - 80) * 2
            recommendations.append("High memory usage")
        factors["resource_usage"] = max(0, resource_score)
        
        # Weighted score
        score = sum(factors[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        
        # Grade
        if score >= 90:
            grade = HealthGrade.A
        elif score >= 80:
            grade = HealthGrade.B
        elif score >= 70:
            grade = HealthGrade.C
        elif score >= 60:
            grade = HealthGrade.D
        else:
            grade = HealthGrade.F
        
        return HealthScore(
            score=round(score, 1),
            grade=grade,
            factors=factors,
            recommendations=recommendations
        )


if __name__ == "__main__":
    calc = HealthScoreCalculator()
    result = calc.calculate(
        uptime_pct=99.5,
        avg_response_ms=150,
        error_rate_pct=1.2,
        recovery_rate_pct=95,
        cpu_pct=45,
        memory_pct=60
    )
    print(f"{result.emoji} Health Score: {result.score} ({result.grade.value})")
    for r in result.recommendations:
        print(f"  → {r}")
