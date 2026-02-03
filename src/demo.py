#!/usr/bin/env python3
"""
AgentMedic Demo
===============
Demonstrates the monitoring, diagnosis, and recovery cycle
with simulated agent failures.

Run: python3 demo.py
"""

import time
import json
from datetime import datetime

from config import register_agent, config
from observer import get_system_status, check_process_running
from diagnoser import analyze, IncidentType
from recoverer import plan_action, execute, RecoveryAction
from verifier import confirm
import logger
import solana_rpc


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(num: int, text: str):
    print(f"\n[Step {num}] {text}")
    print("-" * 40)


def demo_rpc_health():
    """Demo: Check Solana RPC health."""
    print_header("DEMO: Solana RPC Health Check")
    
    print_step(1, "Checking Solana Devnet RPC")
    health = solana_rpc.devnet_health()
    print(f"  Healthy: {health.healthy}")
    print(f"  Current Slot: {health.slot:,}")
    print(f"  Latency: {health.latency_ms}ms")
    
    print_step(2, "Getting recent blockhash")
    blockhash = solana_rpc.get_recent_blockhash()
    print(f"  Blockhash: {blockhash[:20]}..." if blockhash else "  Failed to get blockhash")
    
    return health.healthy


def demo_transaction_check():
    """Demo: Check transaction status."""
    print_header("DEMO: Transaction Inspector")
    
    # Use a known devnet address (Solana Foundation)
    test_address = "11111111111111111111111111111111"  # System program
    
    print_step(1, f"Checking program status: {test_address[:16]}...")
    exists = solana_rpc.check_program_exists(test_address)
    print(f"  Program exists: {exists}")
    
    print_step(2, "Checking account info")
    info = solana_rpc.get_account_info(test_address)
    print(f"  Exists: {info.exists}")
    print(f"  Executable: {info.executable}")
    if info.lamports:
        print(f"  Balance: {info.lamports / 1e9:.4f} SOL")


def demo_simulated_failure():
    """Demo: Simulate an agent failure and recovery."""
    print_header("DEMO: Simulated Agent Failure & Recovery")
    
    # Register a fake agent that will "fail"
    print_step(1, "Registering simulated agent 'test-agent'")
    register_agent(
        name="test-agent",
        process_name="nonexistent-process-12345",  # This won't be running
        health_endpoint=None,
        restart_command="echo 'Simulated restart'",
        max_restarts=3
    )
    print("  Agent registered")
    
    print_step(2, "Running observation cycle")
    status = get_system_status()
    print(f"  Timestamp: {status.timestamp}")
    print(f"  Active incidents: {status.active_incidents}")
    print(f"  RPC healthy: {status.solana_rpc.healthy}")
    
    for name, result in status.agents.items():
        print(f"  Agent '{name}': {result.status.value}")
        if result.errors:
            for err in result.errors:
                print(f"    ⚠ {err}")
    
    print_step(3, "Running diagnosis")
    incidents = analyze(status)
    print(f"  Incidents detected: {len(incidents)}")
    
    for incident in incidents:
        print(f"\n  Incident: {incident.id}")
        print(f"    Type: {incident.incident_type.value}")
        print(f"    Severity: {incident.severity.value}")
        print(f"    Description: {incident.description}")
        print(f"    Requires human: {incident.requires_human}")
        
        # Log incident
        logger.log_incident(incident)
    
    print_step(4, "Planning recovery actions")
    for incident in incidents:
        plan = plan_action(incident)
        print(f"\n  Plan for {incident.id}:")
        print(f"    Action: {plan.action.value}")
        print(f"    Requires human: {plan.requires_human}")
        
        if not plan.requires_human and plan.action != RecoveryAction.NO_ACTION:
            print_step(5, "Executing recovery")
            result = execute(plan)
            print(f"    Status: {result.status.value}")
            print(f"    Message: {result.message}")
            print(f"    Duration: {result.duration_seconds:.2f}s")
            
            print_step(6, "Verifying recovery")
            verification = confirm(plan, result)
            print(f"    Verified: {verification.verified}")
            print(f"    Message: {verification.message}")
            
            # Log recovery
            logger.log_recovery(incident, result, verification)
    
    print_step(7, "Final metrics")
    metrics = logger.get_metrics()
    for k, v in metrics.items():
        print(f"    {k}: {v}")


def demo_full_cycle():
    """Run a complete demo of all capabilities."""
    print("\n" + "=" * 60)
    print("  AgentMedic - Full Demonstration")
    print("  Autonomous Agent Monitoring & Recovery System")
    print("=" * 60)
    print(f"\n  Timestamp: {datetime.utcnow().isoformat()}Z")
    print("  Environment: Solana Devnet (read-only)")
    print("  Mode: Demonstration")
    
    # Run all demos
    demo_rpc_health()
    time.sleep(1)
    
    demo_transaction_check()
    time.sleep(1)
    
    demo_simulated_failure()
    
    print_header("DEMO COMPLETE")
    print("\nThis demonstration showed:")
    print("  ✓ Solana RPC health monitoring")
    print("  ✓ Transaction/account inspection")
    print("  ✓ Agent failure detection")
    print("  ✓ Root cause diagnosis")
    print("  ✓ Automated recovery planning")
    print("  ✓ Recovery execution & verification")
    print("  ✓ Incident logging & metrics")
    print("\nAll operations were read-only and safe.")
    print("No transactions were signed. No funds were handled.")


if __name__ == "__main__":
    demo_full_cycle()
