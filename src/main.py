#!/usr/bin/env python3
"""
AgentMedic - Main Orchestrator
==============================
Autonomous AI agent monitoring, diagnosis, and recovery system.

SAFETY RULES (NEVER BROKEN):
1. Never custody real funds
2. Never sign economic transactions
3. Never expose private keys
4. Read-only on mainnet
5. Devnet for any writes
6. Only report observed data
"""

import sys
import time
import signal
import argparse
from datetime import datetime, timedelta
from typing import List, Optional

from config import config, Intervals, register_agent, list_agents
from observer import get_system_status, SystemStatus
from diagnoser import analyze, Incident
from recoverer import plan_action, execute, RecoveryPlan, RecoveryResult, RecoveryAction
from verifier import confirm
import logger


class AgentMedic:
    """Main orchestrator for agent monitoring and recovery."""
    
    def __init__(self):
        self.running = False
        self.last_healthy_time: Optional[datetime] = None
        self.current_interval = Intervals.DEFAULT
        self.cycle_count = 0
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print("\n[AgentMedic] Shutting down...")
        self.running = False
    
    def _calculate_interval(self, incidents: List[Incident]) -> int:
        """Calculate next check interval based on current state."""
        now = datetime.utcnow()
        
        if incidents:
            # Active incidents: check more frequently
            self.last_healthy_time = None
            return Intervals.INCIDENT
        
        # No incidents
        if self.last_healthy_time is None:
            self.last_healthy_time = now
        
        # Check how long we've been healthy
        healthy_duration = (now - self.last_healthy_time).total_seconds()
        
        if healthy_duration > config.stable_threshold_minutes * 60:
            # Stable for a while: reduce frequency
            return Intervals.STABLE
        
        return Intervals.DEFAULT
    
    def _log_cycle(self, status: SystemStatus, incidents: List[Incident]):
        """Log the monitoring cycle."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        if incidents:
            incident_summary = ", ".join(f"{i.incident_type.value}" for i in incidents)
            print(f"[{timestamp}] INCIDENT: {len(incidents)} issues detected ({incident_summary})")
        else:
            agent_count = len(status.agents)
            rpc_status = "✓" if status.solana_rpc.healthy else "✗"
            print(f"[{timestamp}] HEALTHY: {agent_count} agents monitored, RPC {rpc_status}")
    
    def run_cycle(self) -> tuple[SystemStatus, List[Incident], List[RecoveryResult]]:
        """Run a single monitoring cycle."""
        self.cycle_count += 1
        
        # 1. Observe
        status = get_system_status()
        
        # 2. Diagnose
        incidents = analyze(status)
        
        # 3. Log check
        logger.log_check(status)
        
        # Log incidents
        for incident in incidents:
            logger.log_incident(incident)
        
        # 4. Recover (if needed)
        results = []
        human_alerts = []
        
        for incident in incidents:
            plan = plan_action(incident)
            
            if plan.requires_human:
                human_alerts.append((incident, plan))
                continue
            
            if plan.action != RecoveryAction.NO_ACTION:
                result = execute(plan)
                
                # 5. Verify
                verification = confirm(plan, result)
                
                # 6. Log recovery
                logger.log_recovery(incident, result, verification)
                
                results.append(result)
        
        # Print human alerts
        for incident, plan in human_alerts:
            print(f"\n⚠️  HUMAN INTERVENTION REQUIRED:")
            print(f"   Incident: {incident.id}")
            print(f"   Description: {incident.description}")
            print(f"   Reason: {plan.reason}")
            print(f"   Suggested actions: {', '.join(incident.suggested_actions)}\n")
        
        return status, incidents, results
    
    def run(self, single_cycle: bool = False):
        """Run the main monitoring loop."""
        self.running = True
        
        print("=" * 60)
        print("  AgentMedic - Autonomous Agent Monitoring System")
        print("=" * 60)
        print(f"  Registered agents: {len(list_agents())}")
        print(f"  Solana RPC: {config.solana_rpc}")
        print(f"  Initial interval: {config.check_interval}s")
        print("=" * 60)
        print()
        
        while self.running:
            try:
                status, incidents, results = self.run_cycle()
                self._log_cycle(status, incidents)
                
                if single_cycle:
                    break
                
                # Calculate next interval
                self.current_interval = self._calculate_interval(incidents)
                
                # Wait
                print(f"    Next check in {self.current_interval}s...")
                time.sleep(self.current_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] Cycle failed: {e}")
                time.sleep(30)  # Brief pause before retry
        
        print("\n[AgentMedic] Stopped.")
        print(f"Total cycles: {self.cycle_count}")
        print(f"Metrics: {logger.get_metrics()}")


def main():
    parser = argparse.ArgumentParser(description="AgentMedic - AI Agent Monitoring System")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    parser.add_argument("--status", action="store_true", help="Show current status and exit")
    parser.add_argument("--metrics", action="store_true", help="Show metrics and exit")
    
    args = parser.parse_args()
    
    if args.status:
        status = get_system_status()
        print(f"Timestamp: {status.timestamp}")
        print(f"Active incidents: {status.active_incidents}")
        print(f"Solana RPC: {'Healthy' if status.solana_rpc.healthy else 'Unhealthy'}")
        if status.solana_rpc.healthy:
            print(f"  Slot: {status.solana_rpc.slot}")
            print(f"  Latency: {status.solana_rpc.latency_ms}ms")
        for name, result in status.agents.items():
            print(f"Agent '{name}': {result.status.value}")
        return
    
    if args.metrics:
        metrics = logger.get_metrics()
        print("AgentMedic Metrics")
        print("-" * 40)
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        return
    
    medic = AgentMedic()
    medic.run(single_cycle=args.once)


if __name__ == "__main__":
    main()
