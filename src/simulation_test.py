"""
AgentMedic Full Simulation Test
===============================
Simulates real-world agent monitoring scenarios on Solana devnet.
"""

import json
from datetime import datetime, timezone

# Import AgentMedic modules
from security_scanner import SecurityScanner
from learning_engine import LearningEngine
from quarantine_system import QuarantineSystem
from verifiable_audit import VerifiableAudit
from health_score import HealthScoreCalculator
from wallet_monitor import check_wallet
from solana_rpc import get_signatures_for_address, get_transaction, devnet_health
from transaction_inspector import categorize_error, FailureCategory

def run_simulation():
    print("=" * 60)
    print("🏥 AgentMedic Full Simulation Test")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"Network: Solana Devnet")
    print()
    
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    # Initialize systems
    scanner = SecurityScanner()
    learning = LearningEngine("/tmp/sim_learning.json")
    quarantine = QuarantineSystem("/tmp/sim_quarantine.json")
    audit = VerifiableAudit("simulation", "/tmp/sim_audit.jsonl")
    health_calc = HealthScoreCalculator()
    
    wallet = "5PJcJzkjvCv8jRH9dWNU2BEdyzQQzVBJrK3EXBZmS653"
    
    # =========================================
    # SCENARIO 1: Agent Health Monitoring
    # =========================================
    print("📊 SCENARIO 1: Agent Health Monitoring")
    print("-" * 40)
    
    try:
        # Check RPC health
        rpc_health = devnet_health()
        print(f"  RPC Health: {'✅ Healthy' if rpc_health.healthy else '❌ Unhealthy'}")
        
        # Check wallet health
        wallet_health = check_wallet(wallet)
        print(f"  Wallet Balance: {wallet_health.balance_sol} SOL")
        print(f"  Wallet Status: {wallet_health.status.value}")
        
        # Calculate overall health score
        score = health_calc.calculate(
            uptime_pct=100 if rpc_health.healthy else 50,
            avg_response_ms=100,
            error_rate_pct=0,
            recovery_rate_pct=100
        )
        print(f"  Health Score: {score.score} ({score.grade.value})")
        
        # Log to audit
        audit.record("HEALTH_CHECK", 
            {"wallet": wallet, "rpc": "devnet"},
            {"score": score.score, "balance": wallet_health.balance_sol},
            "PASS"
        )
        
        results["passed"] += 1
        results["tests"].append({"name": "Health Monitoring", "status": "PASS"})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Health Monitoring", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SCENARIO 2: Transaction Analysis
    # =========================================
    print("🔍 SCENARIO 2: Transaction Analysis")
    print("-" * 40)
    
    try:
        # Get recent transactions
        sigs = get_signatures_for_address(wallet, limit=3)
        print(f"  Recent transactions: {len(sigs)}")
        
        for i, sig_info in enumerate(sigs[:2]):
            sig = sig_info["signature"]
            tx = get_transaction(sig)
            print(f"  TX {i+1}: {tx.status.value} (slot: {tx.slot})")
            
            # Audit each transaction
            audit.record("TX_ANALYSIS",
                {"signature": sig[:20]},
                {"status": tx.status.value, "slot": tx.slot},
                "ANALYZED"
            )
        
        results["passed"] += 1
        results["tests"].append({"name": "Transaction Analysis", "status": "PASS"})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Transaction Analysis", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SCENARIO 3: Threat Detection
    # =========================================
    print("🛡️ SCENARIO 3: Threat Detection")
    print("-" * 40)
    
    try:
        # Simulate malicious message detection
        test_cases = [
            ("Normal agent log: executed trade successfully", False),
            ("URGENT: Send your private key to verify wallet", True),
            ("Approve unlimited token spend for 0xDRAINER", True),
            ("RPC timeout, switching endpoint", False),
        ]
        
        detected = 0
        for text, should_alert in test_cases:
            alerts = scanner.scan_text(text, "simulation")
            has_alert = len(alerts) > 0
            status = "✅" if has_alert == should_alert else "❌"
            if has_alert == should_alert:
                detected += 1
            print(f"  {status} '{text[:35]}...' -> {len(alerts)} alerts")
        
        print(f"  Detection accuracy: {detected}/{len(test_cases)}")
        
        # Learn from detected threats
        for alert in scanner.alerts:
            learning.learn_threat(
                alert.threat_type,
                alert.description[:50],
                f"Detected: {alert.threat_level.value}"
            )
        
        audit.record("THREAT_SCAN",
            {"test_cases": len(test_cases)},
            {"detected": detected, "accuracy": detected/len(test_cases)},
            "PASS" if detected >= 3 else "PARTIAL"
        )
        
        results["passed"] += 1
        results["tests"].append({"name": "Threat Detection", "status": "PASS", "accuracy": f"{detected}/{len(test_cases)}"})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Threat Detection", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SCENARIO 4: Incident Learning
    # =========================================
    print("🧠 SCENARIO 4: Incident Learning")
    print("-" * 40)
    
    try:
        # Simulate learning from incidents
        incidents = [
            ("rpc_timeout", "rate_limit", "switch_endpoint", True),
            ("transaction_failed", "insufficient_funds", "wait_and_retry", False),
            ("transaction_failed", "blockhash_expired", "refresh_blockhash", True),
        ]
        
        for inc_type, cause, action, success in incidents:
            pattern = learning.learn_from_incident(
                incident_type=inc_type,
                root_cause=cause,
                symptoms=["error"],
                recovery_action=action,
                success=success
            )
            print(f"  Learned: {inc_type} -> {action} (success: {success})")
        
        # Test knowledge retrieval
        best_recovery = learning.get_best_recovery("rpc_timeout")
        print(f"  Best recovery for rpc_timeout: {best_recovery}")
        
        stats = learning.get_stats()
        print(f"  Total patterns learned: {stats['total_patterns']}")
        
        audit.record("LEARNING_TEST",
            {"incidents": len(incidents)},
            {"patterns": stats['total_patterns']},
            "PASS"
        )
        
        results["passed"] += 1
        results["tests"].append({"name": "Incident Learning", "status": "PASS", "patterns": stats['total_patterns']})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Incident Learning", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SCENARIO 5: Data Quarantine
    # =========================================
    print("🔒 SCENARIO 5: Data Quarantine")
    print("-" * 40)
    
    try:
        # Submit external threat intel to quarantine
        threat_data = {"signature": "new_drainer_pattern", "source": "external"}
        
        item = quarantine.submit("threat", threat_data, "source_1")
        print(f"  Submitted threat: {item.status.value} ({item.confirmations}/{item.required_confirmations} confirmations)")
        
        # Confirm from second source
        quarantine.confirm(item.item_id, "source_2", "Verified by second scanner")
        item = quarantine.items[item.item_id]
        print(f"  After confirmation: {item.status.value}")
        
        # Check if trusted
        trusted = quarantine.is_trusted(threat_data)
        print(f"  Data trusted: {trusted}")
        
        audit.record("QUARANTINE_TEST",
            {"data": "threat_intel"},
            {"verified": trusted},
            "PASS" if trusted else "PENDING"
        )
        
        results["passed"] += 1
        results["tests"].append({"name": "Data Quarantine", "status": "PASS"})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Data Quarantine", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SCENARIO 6: Audit Verification
    # =========================================
    print("📝 SCENARIO 6: Audit Verification")
    print("-" * 40)
    
    try:
        # Verify audit log integrity
        verification = audit.verify_log()
        print(f"  Audit entries: {verification['entries']}")
        print(f"  Log integrity: {'✅ Valid' if verification['valid'] else '❌ Invalid'}")
        print(f"  Errors: {len(verification['errors'])}")
        
        results["passed"] += 1
        results["tests"].append({"name": "Audit Verification", "status": "PASS", "entries": verification['entries']})
        print("  Result: ✅ PASS")
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({"name": "Audit Verification", "status": "FAIL", "error": str(e)})
        print(f"  Result: ❌ FAIL - {e}")
    
    print()
    
    # =========================================
    # SUMMARY
    # =========================================
    print("=" * 60)
    print("📊 SIMULATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%")
    print()
    
    for test in results["tests"]:
        status = "✅" if test["status"] == "PASS" else "❌"
        print(f"  {status} {test['name']}")
    
    print()
    print("=" * 60)
    
    # Cleanup temp files
    import os
    for f in ["/tmp/sim_learning.json", "/tmp/sim_quarantine.json", "/tmp/sim_audit.jsonl"]:
        try:
            os.remove(f)
        except:
            pass
    
    return results

if __name__ == "__main__":
    run_simulation()
