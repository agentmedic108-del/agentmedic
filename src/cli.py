#!/usr/bin/env python3
"""
AgentMedic CLI
==============
Command-line interface for agent monitoring and management.

Usage:
    python3 cli.py status          # Show system status
    python3 cli.py check           # Run one observation cycle
    python3 cli.py metrics         # Show metrics summary
    python3 cli.py rpc             # Check Solana RPC health
    python3 cli.py add <name> <process>  # Register an agent
"""

import sys
import json
from datetime import datetime

from config import register_agent, list_agents, get_agent
from observer import get_system_status
from diagnoser import analyze
from recoverer import plan_action, RecoveryAction
import solana_rpc
import logger


def cmd_status():
    """Show current system status."""
    status = get_system_status()
    
    print(f"\n{'═' * 50}")
    print(f"  AgentMedic Status")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'═' * 50}\n")
    
    # RPC Status
    rpc = status.solana_rpc
    rpc_icon = "✅" if rpc.healthy else "❌"
    print(f"Solana RPC: {rpc_icon} {'Healthy' if rpc.healthy else 'Down'}")
    if rpc.healthy:
        print(f"  Slot: {rpc.slot:,}")
        print(f"  Latency: {rpc.latency_ms}ms")
    
    # Agents
    print(f"\nAgents ({len(status.agents)}):")
    if not status.agents:
        print("  No agents registered")
    for name, result in status.agents.items():
        icon = "✅" if result.status.value == "healthy" else "❌"
        print(f"  {icon} {name}: {result.status.value}")
        for err in result.errors:
            print(f"     └─ {err}")
    
    # Summary
    print(f"\nActive Incidents: {status.active_incidents}")
    print()


def cmd_check():
    """Run a single observation cycle with diagnosis."""
    print("\n[OBSERVE]")
    status = get_system_status()
    logger.log_check(status)
    
    for name, result in status.agents.items():
        print(f"  {name}: {result.status.value}")
    
    print("\n[DIAGNOSE]")
    incidents = analyze(status)
    
    if not incidents:
        print("  No incidents detected")
    else:
        for inc in incidents:
            print(f"  {inc.id}: {inc.incident_type.value}")
            print(f"    {inc.description}")
            logger.log_incident(inc)
            
            plan = plan_action(inc)
            print(f"    Plan: {plan.action.value}")
            if plan.requires_human:
                print(f"    ⚠️  Human required: {plan.reason}")
    
    print()


def cmd_metrics():
    """Show metrics summary."""
    metrics = logger.get_metrics()
    
    print(f"\n{'═' * 50}")
    print(f"  AgentMedic Metrics")
    print(f"{'═' * 50}\n")
    
    print(f"Started: {metrics.get('started_at', 'N/A')}")
    print(f"Total Checks: {metrics['total_checks']}")
    print(f"Uptime: {metrics['uptime_percent']}%")
    print(f"\nIncidents: {metrics['total_incidents']}")
    print(f"Recoveries: {metrics['total_recoveries']}")
    print(f"Recovery Success Rate: {metrics['recovery_success_rate']}%")
    print(f"Mean Time to Recovery: {metrics['mttr_seconds']}s")
    print(f"False Positive Rate: {metrics['false_positive_rate']}%")
    print()


def cmd_rpc():
    """Check Solana RPC health."""
    print("\n[Solana RPC Health Check]")
    
    print("\nDevnet:")
    h = solana_rpc.devnet_health()
    print(f"  Healthy: {h.healthy}")
    if h.healthy:
        print(f"  Slot: {h.slot:,}")
        print(f"  Latency: {h.latency_ms}ms")
    else:
        print(f"  Error: {h.error}")
    
    print("\nMainnet (read-only):")
    h = solana_rpc.mainnet_health()
    print(f"  Healthy: {h.healthy}")
    if h.healthy:
        print(f"  Slot: {h.slot:,}")
        print(f"  Latency: {h.latency_ms}ms")
    print()


def cmd_add(name: str, process: str):
    """Register a new agent to monitor."""
    agent = register_agent(name=name, process_name=process)
    print(f"\n✅ Registered agent '{name}'")
    print(f"   Process: {process}")
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        cmd_status()
    elif cmd == "check":
        cmd_check()
    elif cmd == "metrics":
        cmd_metrics()
    elif cmd == "rpc":
        cmd_rpc()
    elif cmd == "add" and len(sys.argv) >= 4:
        cmd_add(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
