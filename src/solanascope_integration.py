"""
SolanaScope Integration for AgentMedic
======================================
Integrates with SolanaScope API for enhanced diagnostics:
- Wallet anomaly detection
- Transaction failure analysis
- Price confidence checks

API: https://solanascope.vercel.app
Credit: clawdbot-prime (Colosseum Hackathon)
"""

import json
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


SOLANASCOPE_BASE = "https://solanascope.vercel.app"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyResult:
    """Result from SolanaScope anomaly detection."""
    address: str
    sol_balance: float
    transactions_analyzed: int
    anomalies: List[Dict[str, Any]]
    anomaly_count: int
    overall_risk: RiskLevel
    
    @classmethod
    def from_api(cls, data: Dict) -> 'AnomalyResult':
        return cls(
            address=data.get("address", ""),
            sol_balance=data.get("solBalance", 0),
            transactions_analyzed=data.get("transactionsAnalyzed", 0),
            anomalies=data.get("anomalies", []),
            anomaly_count=data.get("anomalyCount", 0),
            overall_risk=RiskLevel(data.get("overallRisk", "low"))
        )


@dataclass
class PriceData:
    """Price data from Pyth oracle via SolanaScope."""
    pair: str
    price: float
    confidence: float
    confidence_pct: str
    
    @classmethod
    def from_api(cls, data: Dict) -> 'PriceData':
        return cls(
            pair=data.get("pair", ""),
            price=data.get("price", 0),
            confidence=data.get("confidence", 0),
            confidence_pct=data.get("confidencePct", "0%")
        )


class SolanaScope:
    """
    Client for SolanaScope API.
    
    Used by AgentMedic for enhanced diagnostics:
    - Check if counterparty wallet is suspicious
    - Detect transaction failure patterns
    - Verify price data reliability
    """
    
    def __init__(self, base_url: str = SOLANASCOPE_BASE, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def health_check(self) -> bool:
        """Check if SolanaScope API is available."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/health")
            data = resp.json()
            return data.get("status") == "healthy"
        except Exception as e:
            print(f"[SolanaScope] Health check failed: {e}")
            return False
    
    async def detect_anomaly(self, wallet_address: str) -> Optional[AnomalyResult]:
        """
        Detect anomalies in a wallet's transaction history.
        
        Useful for AgentMedic diagnostics:
        - High failure rate → wallet may have issues
        - Drained wallet → potential security concern
        - Burst activity → possible bot/attack pattern
        """
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.base_url}/detect/anomaly",
                json={"address": wallet_address}
            )
            if resp.status_code == 200:
                return AnomalyResult.from_api(resp.json())
            return None
        except Exception as e:
            print(f"[SolanaScope] Anomaly detection failed: {e}")
            return None
    
    async def get_price(self, pair: str = "SOL/USD") -> Optional[PriceData]:
        """
        Get current price with confidence interval from Pyth oracle.
        
        Useful for AgentMedic diagnostics:
        - High confidence → price data reliable
        - Low confidence → may explain failed swaps
        """
        try:
            client = await self._get_client()
            # URL encode the pair (SOL/USD -> SOL%2FUSD)
            encoded_pair = pair.replace("/", "%2F")
            resp = await client.get(f"{self.base_url}/price/{encoded_pair}")
            if resp.status_code == 200:
                return PriceData.from_api(resp.json())
            return None
        except Exception as e:
            print(f"[SolanaScope] Price fetch failed: {e}")
            return None
    
    async def get_wallet_balance(self, address: str) -> Optional[float]:
        """Get wallet SOL balance."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/wallet/{address}/balance")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("solBalance", 0)
            return None
        except Exception as e:
            print(f"[SolanaScope] Balance fetch failed: {e}")
            return None


# AgentMedic integration functions

async def diagnose_counterparty(wallet_address: str) -> Dict[str, Any]:
    """
    Use SolanaScope to diagnose a counterparty wallet.
    
    Called by AgentMedic when an agent's transaction fails
    to determine if the issue is with the counterparty.
    
    Returns diagnostic info for the agent's incident report.
    """
    scope = SolanaScope()
    result = {
        "wallet": wallet_address,
        "checked": False,
        "risk_level": "unknown",
        "recommendation": "unable to analyze"
    }
    
    try:
        anomaly = await scope.detect_anomaly(wallet_address)
        if anomaly:
            result["checked"] = True
            result["risk_level"] = anomaly.overall_risk.value
            result["anomaly_count"] = anomaly.anomaly_count
            result["sol_balance"] = anomaly.sol_balance
            result["anomalies"] = anomaly.anomalies
            
            # Generate recommendation based on risk
            if anomaly.overall_risk == RiskLevel.CRITICAL:
                result["recommendation"] = "AVOID - Critical risk detected, recommend blacklist"
            elif anomaly.overall_risk == RiskLevel.HIGH:
                result["recommendation"] = "CAUTION - High risk, recommend manual review"
            elif anomaly.overall_risk == RiskLevel.MEDIUM:
                result["recommendation"] = "MONITOR - Medium risk, proceed with caution"
            else:
                result["recommendation"] = "OK - Low risk, normal activity"
    
    finally:
        await scope.close()
    
    return result


async def check_price_reliability(pair: str = "SOL/USD") -> Dict[str, Any]:
    """
    Check if current price data is reliable for trading decisions.
    
    Called by AgentMedic to diagnose if a failed swap was due
    to unreliable price data.
    """
    scope = SolanaScope()
    result = {
        "pair": pair,
        "checked": False,
        "reliable": False,
        "recommendation": "unable to check"
    }
    
    try:
        price = await scope.get_price(pair)
        if price:
            result["checked"] = True
            result["price"] = price.price
            result["confidence"] = price.confidence
            result["confidence_pct"] = price.confidence_pct
            
            # Parse confidence percentage
            conf_pct = float(price.confidence_pct.replace("%", ""))
            
            if conf_pct < 0.5:
                result["reliable"] = True
                result["recommendation"] = "Price data highly reliable"
            elif conf_pct < 1.0:
                result["reliable"] = True
                result["recommendation"] = "Price data reliable, normal confidence"
            elif conf_pct < 2.0:
                result["reliable"] = False
                result["recommendation"] = "Price data uncertain, consider waiting"
            else:
                result["reliable"] = False
                result["recommendation"] = "Price data unreliable, recommend delay"
    
    finally:
        await scope.close()
    
    return result


# Demo function
async def demo():
    """Demonstrate SolanaScope integration."""
    print("=" * 60)
    print("AgentMedic + SolanaScope Integration Demo")
    print("=" * 60)
    
    # Test wallet (example from Solana)
    test_wallet = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"
    
    print(f"\n[1] Checking counterparty wallet: {test_wallet[:20]}...")
    diagnosis = await diagnose_counterparty(test_wallet)
    print(f"    Risk Level: {diagnosis['risk_level']}")
    print(f"    Recommendation: {diagnosis['recommendation']}")
    if diagnosis.get('anomalies'):
        print(f"    Anomalies found: {len(diagnosis['anomalies'])}")
        for a in diagnosis['anomalies']:
            print(f"      - {a['type']}: {a['description']}")
    
    print(f"\n[2] Checking SOL/USD price reliability...")
    price_check = await check_price_reliability("SOL/USD")
    if price_check['checked']:
        print(f"    Price: ${price_check['price']:.2f}")
        print(f"    Confidence: {price_check['confidence_pct']}")
        print(f"    Reliable: {price_check['reliable']}")
        print(f"    Recommendation: {price_check['recommendation']}")
    
    print("\n" + "=" * 60)
    print("Integration demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
