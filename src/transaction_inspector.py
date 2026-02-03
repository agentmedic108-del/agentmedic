"""
Transaction Inspector
=====================
Deep inspection of Solana transactions for failure analysis.
SAFETY: Read-only operations only.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

import solana_rpc


class FailureCategory(Enum):
    """Categories of transaction failures."""
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_INSTRUCTION = "invalid_instruction"
    ACCOUNT_NOT_FOUND = "account_not_found"
    PROGRAM_ERROR = "program_error"
    SIGNATURE_ERROR = "signature_error"
    BLOCKHASH_EXPIRED = "blockhash_expired"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class TransactionAnalysis:
    """Analysis result for a transaction."""
    signature: str
    success: bool
    failure_category: Optional[FailureCategory]
    error_message: Optional[str]
    program_ids: List[str]
    instructions_count: int
    compute_units: Optional[int]
    fee_paid: Optional[int]
    recommendations: List[str]


def categorize_error(error: str) -> FailureCategory:
    """Categorize a transaction error by its message."""
    if not error:
        return FailureCategory.UNKNOWN
    
    error_lower = error.lower()
    
    if "insufficient" in error_lower or "lamports" in error_lower:
        return FailureCategory.INSUFFICIENT_FUNDS
    
    if "invalid instruction" in error_lower or "instruction" in error_lower:
        return FailureCategory.INVALID_INSTRUCTION
    
    if "account" in error_lower and ("not found" in error_lower or "missing" in error_lower):
        return FailureCategory.ACCOUNT_NOT_FOUND
    
    if "program" in error_lower and "error" in error_lower:
        return FailureCategory.PROGRAM_ERROR
    
    if "signature" in error_lower:
        return FailureCategory.SIGNATURE_ERROR
    
    if "blockhash" in error_lower or "expired" in error_lower:
        return FailureCategory.BLOCKHASH_EXPIRED
    
    if "429" in error_lower or "rate" in error_lower:
        return FailureCategory.RATE_LIMITED
    
    if "timeout" in error_lower or "network" in error_lower:
        return FailureCategory.NETWORK_ERROR
    
    return FailureCategory.UNKNOWN


def get_recommendations(category: FailureCategory) -> List[str]:
    """Get recovery recommendations for a failure category."""
    recommendations = {
        FailureCategory.INSUFFICIENT_FUNDS: [
            "Check account balance",
            "Request devnet airdrop if on devnet",
            "Reduce transaction amount"
        ],
        FailureCategory.INVALID_INSTRUCTION: [
            "Verify instruction data format",
            "Check account permissions",
            "Review program documentation"
        ],
        FailureCategory.ACCOUNT_NOT_FOUND: [
            "Verify account address",
            "Ensure account is initialized",
            "Check if account was closed"
        ],
        FailureCategory.PROGRAM_ERROR: [
            "Check program logs for details",
            "Verify input parameters",
            "Ensure correct program version"
        ],
        FailureCategory.SIGNATURE_ERROR: [
            "Verify signer keys",
            "Check transaction signing order",
            "Ensure all required signers present"
        ],
        FailureCategory.BLOCKHASH_EXPIRED: [
            "Retry with fresh blockhash",
            "Reduce transaction preparation time",
            "Use durable nonces for long-lived transactions"
        ],
        FailureCategory.RATE_LIMITED: [
            "Apply cooldown period",
            "Switch to backup RPC endpoint",
            "Implement exponential backoff"
        ],
        FailureCategory.NETWORK_ERROR: [
            "Retry request",
            "Check network connectivity",
            "Try alternative RPC endpoint"
        ],
        FailureCategory.UNKNOWN: [
            "Check transaction logs",
            "Review error details",
            "Consult documentation"
        ]
    }
    return recommendations.get(category, recommendations[FailureCategory.UNKNOWN])


def analyze_transaction(
    signature: str, 
    rpc_url: str = solana_rpc.DEVNET_RPC
) -> TransactionAnalysis:
    """Perform deep analysis of a transaction."""
    
    tx_result = solana_rpc.get_transaction(signature, rpc_url)
    
    if tx_result.status == solana_rpc.TransactionStatus.NOT_FOUND:
        return TransactionAnalysis(
            signature=signature,
            success=False,
            failure_category=FailureCategory.UNKNOWN,
            error_message="Transaction not found",
            program_ids=[],
            instructions_count=0,
            compute_units=None,
            fee_paid=None,
            recommendations=["Verify signature is correct", "Transaction may not be confirmed yet"]
        )
    
    success = tx_result.status == solana_rpc.TransactionStatus.SUCCESS
    
    failure_category = None
    recommendations = []
    
    if not success and tx_result.error:
        failure_category = categorize_error(tx_result.error)
        recommendations = get_recommendations(failure_category)
    
    # Extract program IDs from logs
    program_ids = []
    if tx_result.logs:
        for log in tx_result.logs:
            if "Program " in log and " invoke" in log:
                # Extract program ID from "Program <id> invoke [N]"
                parts = log.split()
                if len(parts) >= 2:
                    program_ids.append(parts[1])
    
    # Deduplicate program IDs
    program_ids = list(dict.fromkeys(program_ids))
    
    return TransactionAnalysis(
        signature=signature,
        success=success,
        failure_category=failure_category,
        error_message=tx_result.error,
        program_ids=program_ids,
        instructions_count=len(program_ids),  # Approximation
        compute_units=None,  # Would need parsed transaction data
        fee_paid=tx_result.fee,
        recommendations=recommendations
    )


def analyze_recent_failures(
    address: str,
    limit: int = 10,
    rpc_url: str = solana_rpc.DEVNET_RPC
) -> Dict[str, Any]:
    """Analyze recent transaction failures for an address."""
    
    signatures = solana_rpc.get_signatures_for_address(address, limit, rpc_url)
    
    results = {
        "address": address,
        "total_checked": len(signatures),
        "successful": 0,
        "failed": 0,
        "failure_breakdown": {},
        "failures": []
    }
    
    for sig_info in signatures:
        if sig_info.get("err"):
            results["failed"] += 1
            
            # Analyze the failure
            analysis = analyze_transaction(sig_info["signature"], rpc_url)
            
            if analysis.failure_category:
                cat = analysis.failure_category.value
                results["failure_breakdown"][cat] = results["failure_breakdown"].get(cat, 0) + 1
            
            results["failures"].append({
                "signature": sig_info["signature"],
                "category": analysis.failure_category.value if analysis.failure_category else "unknown",
                "error": analysis.error_message,
                "recommendations": analysis.recommendations
            })
        else:
            results["successful"] += 1
    
    return results


# CLI for testing
if __name__ == "__main__":
    import sys
    
    print("Transaction Inspector")
    print("-" * 40)
    
    # Check RPC health first
    health = solana_rpc.devnet_health()
    print(f"Devnet RPC: {'✅ Healthy' if health.healthy else '❌ Down'}")
    
    if len(sys.argv) > 1:
        sig = sys.argv[1]
        print(f"\nAnalyzing: {sig[:20]}...")
        analysis = analyze_transaction(sig)
        print(f"Success: {analysis.success}")
        if not analysis.success:
            print(f"Category: {analysis.failure_category.value if analysis.failure_category else 'N/A'}")
            print(f"Error: {analysis.error_message}")
            print("Recommendations:")
            for r in analysis.recommendations:
                print(f"  - {r}")
