#!/usr/bin/env python3
"""
AgentMedic - Main Orchestrator (v3 - Gemini Hybrid)
=====================================================

Autonomous AI agent monitoring, diagnosis, and recovery system.

ARCHITECTURE:
  Heartbeat (local) -> 0 tokens, keeps bot alive
  Gemini Flash -> cheap analysis on alerts and deep checks
  Claude (openclaw) -> only for complex decisions, keeps memory

TOKEN SAVINGS:
  Before: Claude every 10 min = ~144 calls/day = $$$
  After:  Gemini for routine = centavos, Claude only when needed

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
import subprocess
from datetime import datetime, timedelta
from typing import List, Optional

from config import config, Intervals, register_agent, list_agents
from observer import get_system_status, SystemStatus
from diagnoser import analyze, Incident
from recoverer import plan_action, execute, RecoveryPlan, RecoveryResult, RecoveryAction
from verifier import confirm
from heartbeat import create_default_heartbeat, Heartbeat
import logger


class AgentMedic:
    """Main orchestrator for agent monitoring and recovery."""

    def __init__(self):
        self.running = False
        self.last_healthy_time: Optional[datetime] = None
        self.current_interval = Intervals.DEFAULT
        self.cycle_count = 0
        self.gemini_check_count = 0

        # --- Heartbeat with Gemini ---
        self.heartbeat = create_default_heartbeat()

        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print("\n[AgentMedic] Shutting down...")
        self.running = False
        self.heartbeat.stop()

    def _calculate_interval(self, incidents: List[Incident]) -> int:
        """Calculate next check interval based on current state."""
        now = datetime.utcnow()

        if incidents:
            self.last_healthy_time = None
            return Intervals.INCIDENT

        if self.last_healthy_time is None:
            self.last_healthy_time = now

        healthy_duration = (now - self.last_healthy_time).total_seconds()

        if healthy_duration > config.stable_threshold_minutes * 60:
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
        """
        Run a single monitoring cycle.
        Uses Claude (tokens) - only called when Gemini escalates or forced.
        """
        self.cycle_count += 1
        print(f"\n  🧠 Claude AI Cycle #{self.cycle_count} (Claude tokens consumed)")

        # 1. Observe
        status = get_system_status()

        # 2. Diagnose
        incidents = analyze(status)

        # 3. Log check
        logger.log_check(status)

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
                verification = confirm(plan, result)
                results.append(result)

        for incident, plan in human_alerts:
            print(f"\n⚠️ HUMAN INTERVENTION REQUIRED:")
            print(f"   Incident: {incident.id}")
            print(f"   Description: {incident.description}")
            print(f"   Reason: {plan.reason}")
            print(f"   Suggested actions: {', '.join(incident.suggested_actions)}\n")

        return status, incidents, results

    def run_gemini_check(self) -> bool:
        """
        Run a deep check using Gemini Flash (cheap).
        Returns True if Claude needs to be involved.
        """
        self.gemini_check_count += 1
        print(f"\n  🔍 Gemini Deep Check #{self.gemini_check_count} (centavos)")

        try:
            from gemini_bridge import analyze_health_data

            # Get system status (local, no AI tokens)
            status = get_system_status()

            # Build data for Gemini
            health_data = {
                "solana_rpc_healthy": status.solana_rpc.healthy,
                "solana_rpc_slot": status.solana_rpc.slot if status.solana_rpc.healthy else None,
                "solana_rpc_latency": status.solana_rpc.latency_ms if status.solana_rpc.healthy else None,
                "active_incidents": status.active_incidents,
                "agents_count": len(status.agents),
                "agents_status": {name: result.status.value for name, result in status.agents.items()},
                "timestamp": status.timestamp,
            }

            analysis = analyze_health_data(health_data)

            severity = analysis.get("severity", "unknown")
            action = analysis.get("action", "none")
            needs_claude = analysis.get("needs_claude", False)
            summary = analysis.get("summary", "No summary")

            print(f"  🔍 Gemini result: {severity} | {summary}")

            # Log the check
            logger.log_check(status)

            # If Gemini says escalate to Claude
            if needs_claude or action == "escalate_to_claude":
                print(f"  🔍 Gemini escalating to Claude: {analysis.get('reason', 'complex issue')}")
                return True

            # If Gemini says alert human directly
            if action == "alert_human" and severity == "critical":
                event_text = f"GEMINI ALERT: {summary}"
                subprocess.run(
                    ["openclaw", "system", "event", "--text", event_text, "--mode", "now"],
                    timeout=15,
                    capture_output=True,
                    text=True
                )

            return False

        except ImportError:
            print("  ⚠️ gemini_bridge not found, falling back to Claude")
            return True
        except Exception as e:
            print(f"  ⚠️ Gemini check failed: {e}, falling back to Claude")
            return True

    def run(self, single_cycle: bool = False):
        """
        Run the main monitoring loop with Gemini hybrid.

        Flow:
            1. Heartbeat every 30s (0 tokens)
            2. If alert -> Gemini analyzes (centavos)
            3. If Gemini says complex -> Claude via openclaw (tokens)
            4. Deep check every 30 min via Gemini (centavos)
            5. Claude only when truly needed (preserves memory)
        """
        self.running = True

        # Test Gemini connection
        gemini_ok = False
        try:
            from gemini_bridge import test_gemini_connection
            gemini_ok = test_gemini_connection()
        except ImportError:
            print("  ⚠️ gemini_bridge.py not found")

        print("=" * 60)
        print("  AgentMedic - Autonomous Agent Monitoring System")
        print("  💓 Heartbeat + 🔍 Gemini + 🧠 Claude Hybrid")
        print("=" * 60)
        print(f"  Registered agents: {len(list_agents())}")
        print(f"  Solana RPC: {config.solana_rpc}")
        print(f"  Heartbeat: every {self.heartbeat.interval}s (free)")
        print(f"  Gemini Flash: {'✅ connected' if gemini_ok else '❌ not connected'}")
        print(f"  Claude: only when Gemini escalates")
        print(f"  Deep check: every {Intervals.STABLE}s via Gemini (centavos)")
        print("=" * 60)
        print()

        if single_cycle:
            status, incidents, results = self.run_cycle()
            self._log_cycle(status, incidents)
            return

        # --- Continuous mode ---
        last_deep_check = time.time()
        deep_check_interval = Intervals.STABLE

        while self.running:
            try:
                # === HEARTBEAT (0 tokens) ===
                hb_result = self.heartbeat.beat()

                now = time.time()
                time_since_deep = now - last_deep_check
                needs_deep_check = time_since_deep >= deep_check_interval

                # === DEEP CHECK via Gemini (centavos) ===
                if needs_deep_check:
                    needs_claude = self.run_gemini_check()
                    last_deep_check = now

                    if needs_claude:
                        print(f"\n  ⚡ Gemini escalated to Claude")
                        status, incidents, results = self.run_cycle()
                        self._log_cycle(status, incidents)
                        self.heartbeat.mark_ai_called()
                        deep_check_interval = self._calculate_interval(incidents)
                    else:
                        print(f"  ✅ Gemini handled it, Claude not needed")
                        deep_check_interval = Intervals.STABLE

                    print(f"  ⏱️  Next deep check in {deep_check_interval}s")

                # === ALERT handled by heartbeat + Gemini automatically ===
                # (heartbeat.beat() already calls Gemini and wakes Claude if needed)

                # === SLEEP ===
                time.sleep(self.heartbeat.interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] Cycle failed: {e}")
                time.sleep(30)

        print("\n[AgentMedic] Stopped.")
        print(f"Total Claude cycles: {self.cycle_count}")
        print(f"Total Gemini checks: {self.gemini_check_count}")
        print(f"Total heartbeats: {self.heartbeat.beat_count}")
        print(f"Gemini calls: {self.heartbeat.state['total_gemini_calls']}")
        print(f"Claude wakes: {self.heartbeat.state['total_claude_wakes']}")
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
