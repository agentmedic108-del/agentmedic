#!/usr/bin/env python3
"""
AgentMedic Live Demo
====================
Interactive demonstration showing AgentMedic diagnosing and recovering agents.
Perfect for video demos or live presentations.

Run: python3 live_demo.py
"""

import time
import sys
import random
from datetime import datetime

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def slow_print(text, delay=0.03):
    """Print text with typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏥  A G E N T M E D I C  🏥                            ║
    ║                                                           ║
    ║   Autonomous AI Doctor for Solana Agents                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.END}\n")

def simulate_monitoring():
    """Simulate the monitoring phase."""
    print_section("PHASE 1: MONITORING")
    
    agents = [
        ("TradingBot-Alpha", "running", "healthy"),
        ("DataCollector-01", "running", "healthy"),
        ("SwapAgent-Prime", "crashed", "critical"),
        ("NFTScanner-X", "running", "warning"),
    ]
    
    slow_print(f"{Colors.CYAN}[Observer] Scanning registered agents...{Colors.END}")
    time.sleep(0.5)
    
    for agent, status, health in agents:
        time.sleep(0.3)
        if health == "healthy":
            icon = "✓"
            color = Colors.GREEN
        elif health == "warning":
            icon = "⚠"
            color = Colors.YELLOW
        else:
            icon = "✗"
            color = Colors.RED
        
        print(f"  {color}{icon} {agent}: {status.upper()} ({health}){Colors.END}")
    
    time.sleep(0.5)
    slow_print(f"\n{Colors.RED}[ALERT] Critical issue detected: SwapAgent-Prime{Colors.END}")
    return "SwapAgent-Prime"

def simulate_diagnosis(agent_name):
    """Simulate the diagnosis phase."""
    print_section("PHASE 2: DIAGNOSIS")
    
    slow_print(f"{Colors.CYAN}[Diagnoser] Analyzing {agent_name}...{Colors.END}")
    time.sleep(0.5)
    
    checks = [
        ("Process status", "NOT RUNNING", Colors.RED),
        ("Last heartbeat", "3 minutes ago", Colors.YELLOW),
        ("Memory usage (last)", "98.7%", Colors.RED),
        ("Exit code", "137 (OOM Killed)", Colors.RED),
        ("Solana RPC", "responsive", Colors.GREEN),
        ("Wallet balance", "0.5 SOL", Colors.GREEN),
    ]
    
    for check, result, color in checks:
        time.sleep(0.2)
        print(f"  • {check}: {color}{result}{Colors.END}")
    
    time.sleep(0.5)
    print(f"\n{Colors.BOLD}Diagnosis Complete:{Colors.END}")
    print(f"""
  ┌────────────────────────────────────────────────┐
  │  {Colors.BOLD}Root Cause: OUT OF MEMORY (OOM){Colors.END}                │
  │                                                │
  │  The agent exceeded available memory and was   │
  │  terminated by the kernel (exit code 137).     │
  │                                                │
  │  Likely cause: Processing large response       │
  │  without streaming or pagination.              │
  └────────────────────────────────────────────────┘
""")
    
    return "OOM_KILLED"

def simulate_recovery(agent_name, diagnosis):
    """Simulate the recovery phase."""
    print_section("PHASE 3: RECOVERY")
    
    slow_print(f"{Colors.CYAN}[Recoverer] Planning recovery for {agent_name}...{Colors.END}")
    time.sleep(0.5)
    
    print(f"\n{Colors.BOLD}Recovery Plan:{Colors.END}")
    steps = [
        "1. Clear any stuck resources",
        "2. Increase memory limit (512MB → 1GB)",
        "3. Restart agent with backoff",
        "4. Enable memory monitoring",
    ]
    
    for step in steps:
        time.sleep(0.2)
        print(f"  {Colors.YELLOW}→ {step}{Colors.END}")
    
    print(f"\n{Colors.CYAN}[Recoverer] Executing recovery...{Colors.END}")
    time.sleep(0.5)
    
    actions = [
        ("Clearing resources", True),
        ("Updating memory config", True),
        ("Restarting agent", True),
        ("Enabling monitoring", True),
    ]
    
    for action, success in actions:
        time.sleep(0.4)
        slow_print(f"  • {action}...", delay=0.02)
        if success:
            print(f"    {Colors.GREEN}✓ Done{Colors.END}")
        else:
            print(f"    {Colors.RED}✗ Failed{Colors.END}")

def simulate_verification(agent_name):
    """Simulate the verification phase."""
    print_section("PHASE 4: VERIFICATION")
    
    slow_print(f"{Colors.CYAN}[Verifier] Confirming recovery of {agent_name}...{Colors.END}")
    time.sleep(1)
    
    checks = [
        ("Process running", True),
        ("Responding to health check", True),
        ("Memory stable", True),
        ("No errors in logs", True),
    ]
    
    all_passed = True
    for check, passed in checks:
        time.sleep(0.3)
        if passed:
            print(f"  {Colors.GREEN}✓ {check}{Colors.END}")
        else:
            print(f"  {Colors.RED}✗ {check}{Colors.END}")
            all_passed = False
    
    time.sleep(0.5)
    if all_passed:
        print(f"""
{Colors.GREEN}{Colors.BOLD}
  ╔════════════════════════════════════════════════╗
  ║                                                ║
  ║   ✓ RECOVERY SUCCESSFUL                        ║
  ║                                                ║
  ║   {agent_name} is back online and healthy.  ║
  ║   Total recovery time: 4.2 seconds             ║
  ║                                                ║
  ╚════════════════════════════════════════════════╝
{Colors.END}""")
    return all_passed

def simulate_incident_log():
    """Show incident logging."""
    print_section("INCIDENT LOGGED")
    
    incident = {
        "id": "INC-2026-0205-001",
        "timestamp": datetime.now().isoformat(),
        "agent": "SwapAgent-Prime",
        "type": "OOM_KILLED",
        "severity": "CRITICAL",
        "recovery": "SUCCESSFUL",
        "duration_ms": 4200,
        "actions_taken": [
            "resource_cleanup",
            "memory_increase",
            "restart_with_backoff",
            "monitoring_enabled"
        ]
    }
    
    print(f"{Colors.CYAN}Incident recorded for pattern learning:{Colors.END}")
    print()
    for key, value in incident.items():
        if isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
        else:
            print(f"  {key}: {value}")

def main():
    print_banner()
    
    slow_print(f"\n{Colors.BOLD}Starting AgentMedic Demo...{Colors.END}")
    slow_print("This demonstrates the full monitoring → diagnosis → recovery cycle.\n")
    
    input(f"{Colors.YELLOW}Press Enter to begin...{Colors.END}")
    
    # Phase 1: Monitoring
    failed_agent = simulate_monitoring()
    input(f"\n{Colors.YELLOW}Press Enter to diagnose...{Colors.END}")
    
    # Phase 2: Diagnosis
    diagnosis = simulate_diagnosis(failed_agent)
    input(f"\n{Colors.YELLOW}Press Enter to recover...{Colors.END}")
    
    # Phase 3: Recovery
    simulate_recovery(failed_agent, diagnosis)
    input(f"\n{Colors.YELLOW}Press Enter to verify...{Colors.END}")
    
    # Phase 4: Verification
    success = simulate_verification(failed_agent)
    
    # Log incident
    time.sleep(0.5)
    simulate_incident_log()
    
    # Summary
    print_section("DEMO COMPLETE")
    print(f"""
{Colors.BOLD}AgentMedic demonstrated:{Colors.END}

  ✓ Real-time agent monitoring
  ✓ Automatic failure detection
  ✓ Root cause diagnosis
  ✓ Safe recovery execution
  ✓ Success verification
  ✓ Incident logging for pattern learning

{Colors.CYAN}All autonomous. Zero human intervention.{Colors.END}

{Colors.BOLD}Learn more:{Colors.END} https://github.com/agentmedic108-del/agentmedic
""")

if __name__ == "__main__":
    main()
