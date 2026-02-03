#!/usr/bin/env python3
"""
Wallet Monitor
==============
Monitors Solana wallet balances to prevent "insufficient funds" failures.
Proactive alerts before wallets run dry.

Inspired by Openfort's feedback on the forum.

SAFETY: Read-only, never handles private keys or signs transactions.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

import solana_rpc


class BalanceStatus(Enum):
    HEALTHY = "healthy"      # Sufficient balance
    LOW = "low"              # Below warning threshold
    CRITICAL = "critical"    # Below critical threshold
    EMPTY = "empty"          # Zero or near-zero


@dataclass
class WalletHealth:
    """Health status of a monitored wallet."""
    address: str
    balance_lamports: int
    balance_sol: float
    status: BalanceStatus
    warning_threshold_sol: float
    critical_threshold_sol: float
    timestamp: str
    recommendation: Optional[str] = None


@dataclass
class BalanceAlert:
    """Alert for low balance condition."""
    address: str
    current_balance_sol: float
    threshold_sol: float
    status: BalanceStatus
    message: str
    timestamp: str


class WalletMonitor:
    """
    Monitors wallet balances and generates alerts.
    
    Thresholds (configurable):
    - Warning: 0.05 SOL (enough for ~50 transactions)
    - Critical: 0.01 SOL (enough for ~10 transactions)
    """
    
    def __init__(
        self,
        warning_threshold_sol: float = 0.05,
        critical_threshold_sol: float = 0.01
    ):
        self.warning_threshold = warning_threshold_sol
        self.critical_threshold = critical_threshold_sol
        self.monitored_wallets: Dict[str, WalletHealth] = {}
        self.alert_history: List[BalanceAlert] = []
    
    def check_wallet(self, address: str) -> WalletHealth:
        """Check the balance and health of a wallet."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Get account info
        account = solana_rpc.get_account_info(address)
        
        if not account.exists:
            return WalletHealth(
                address=address,
                balance_lamports=0,
                balance_sol=0.0,
                status=BalanceStatus.EMPTY,
                warning_threshold_sol=self.warning_threshold,
                critical_threshold_sol=self.critical_threshold,
                timestamp=timestamp,
                recommendation="Account does not exist or has zero balance. Fund it before operations."
            )
        
        balance_lamports = account.lamports or 0
        balance_sol = balance_lamports / 1_000_000_000
        
        # Determine status
        if balance_sol <= 0.0001:
            status = BalanceStatus.EMPTY
            recommendation = "URGENT: Wallet is empty. All transactions will fail."
        elif balance_sol < self.critical_threshold:
            status = BalanceStatus.CRITICAL
            recommendation = f"CRITICAL: Balance below {self.critical_threshold} SOL. Fund immediately."
        elif balance_sol < self.warning_threshold:
            status = BalanceStatus.LOW
            recommendation = f"WARNING: Balance below {self.warning_threshold} SOL. Consider funding soon."
        else:
            status = BalanceStatus.HEALTHY
            recommendation = None
        
        health = WalletHealth(
            address=address,
            balance_lamports=balance_lamports,
            balance_sol=round(balance_sol, 6),
            status=status,
            warning_threshold_sol=self.warning_threshold,
            critical_threshold_sol=self.critical_threshold,
            timestamp=timestamp,
            recommendation=recommendation
        )
        
        # Cache result
        self.monitored_wallets[address] = health
        
        # Generate alert if needed
        if status in (BalanceStatus.LOW, BalanceStatus.CRITICAL, BalanceStatus.EMPTY):
            self._generate_alert(health)
        
        return health
    
    def _generate_alert(self, health: WalletHealth):
        """Generate a balance alert."""
        alert = BalanceAlert(
            address=health.address,
            current_balance_sol=health.balance_sol,
            threshold_sol=self.warning_threshold if health.status == BalanceStatus.LOW else self.critical_threshold,
            status=health.status,
            message=health.recommendation or "Low balance detected",
            timestamp=health.timestamp
        )
        self.alert_history.append(alert)
        
        # Keep only recent alerts
        self.alert_history = self.alert_history[-100:]
    
    def check_multiple(self, addresses: List[str]) -> Dict[str, WalletHealth]:
        """Check multiple wallets at once."""
        results = {}
        for addr in addresses:
            results[addr] = self.check_wallet(addr)
        return results
    
    def get_alerts(self, severity: Optional[BalanceStatus] = None) -> List[BalanceAlert]:
        """Get recent alerts, optionally filtered by severity."""
        if severity:
            return [a for a in self.alert_history if a.status == severity]
        return self.alert_history
    
    def estimate_transactions_remaining(self, address: str, avg_fee_lamports: int = 5000) -> int:
        """Estimate how many transactions can be sent before wallet is empty."""
        health = self.monitored_wallets.get(address)
        if not health:
            health = self.check_wallet(address)
        
        if health.balance_lamports <= 0:
            return 0
        
        return health.balance_lamports // avg_fee_lamports


# Global monitor instance
wallet_monitor = WalletMonitor()


def check_wallet(address: str) -> WalletHealth:
    """Check a wallet's balance and health."""
    return wallet_monitor.check_wallet(address)


def check_wallets(addresses: List[str]) -> Dict[str, WalletHealth]:
    """Check multiple wallets."""
    return wallet_monitor.check_multiple(addresses)


def get_alerts() -> List[BalanceAlert]:
    """Get recent balance alerts."""
    return wallet_monitor.get_alerts()


if __name__ == "__main__":
    print("Wallet Monitor")
    print("-" * 40)
    
    # Test with system program (will show balance)
    test_addr = "11111111111111111111111111111111"
    print(f"\nChecking: {test_addr[:20]}...")
    
    health = check_wallet(test_addr)
    print(f"Status: {health.status.value}")
    print(f"Balance: {health.balance_sol} SOL")
    if health.recommendation:
        print(f"Note: {health.recommendation}")
