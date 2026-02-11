"""
Solana RPC Integration
======================
Read-only queries to Solana devnet (and optionally mainnet).
SAFETY: Never signs transactions, never handles private keys.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

DEVNET_RPC = "https://api.devnet.solana.com"

# CRITICAL SECURITY: Mainnet write protection
def _validate_mainnet_write_forbidden(operation: str, rpc_url: str):
    """
    Enforce read-only access on mainnet.
    Raises exception if attempting write operations on mainnet.
    """
    WRITE_OPERATIONS = [
        "sendTransaction",
        "simulateTransaction", 
        "requestAirdrop"
    ]
    
    is_mainnet = "mainnet" in rpc_url.lower()
    is_write_op = operation in WRITE_OPERATIONS
    
    if is_mainnet and is_write_op:
        raise PermissionError(
            f"BLOCKED: Write operation '{operation}' not allowed on mainnet. "
            f"AgentMedic is read-only on mainnet for safety."
        )

MAINNET_RPC = "https://api.mainnet-beta.solana.com"

class TransactionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    PENDING = "pending"

@dataclass
class TransactionResult:
    signature: str
    status: TransactionStatus
    slot: Optional[int] = None
    error: Optional[str] = None
    logs: Optional[List[str]] = None
    fee: Optional[int] = None
    block_time: Optional[int] = None

@dataclass
class AccountInfo:
    address: str
    exists: bool
    lamports: Optional[int] = None
    owner: Optional[str] = None
    executable: bool = False
    data_len: Optional[int] = None

@dataclass
class RPCHealth:
    healthy: bool
    slot: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


def _rpc_call(method: str, params: List[Any], rpc_url: str = DEVNET_RPC) -> Dict:
    """Make a JSON-RPC call to Solana."""
    # Validate mainnet write protection
    _validate_mainnet_write_forbidden(method, rpc_url)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", rpc_url,
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=30
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": {"message": str(e)}}


def check_rpc_health(rpc_url: str = DEVNET_RPC) -> RPCHealth:
    """Check if Solana RPC is healthy and get current slot."""
    import time
    start = time.time()
    
    response = _rpc_call("getSlot", [], rpc_url)
    latency = (time.time() - start) * 1000
    
    if "error" in response:
        return RPCHealth(
            healthy=False,
            error=response["error"].get("message", "Unknown error")
        )
    
    return RPCHealth(
        healthy=True,
        slot=response.get("result"),
        latency_ms=round(latency, 2)
    )


def get_transaction(signature: str, rpc_url: str = DEVNET_RPC) -> TransactionResult:
    """Get transaction details by signature."""
    response = _rpc_call(
        "getTransaction",
        [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}],
        rpc_url
    )
    
    if "error" in response:
        return TransactionResult(
            signature=signature,
            status=TransactionStatus.NOT_FOUND,
            error=response["error"].get("message")
        )
    
    result = response.get("result")
    if result is None:
        return TransactionResult(
            signature=signature,
            status=TransactionStatus.NOT_FOUND
        )
    
    meta = result.get("meta", {})
    err = meta.get("err")
    
    return TransactionResult(
        signature=signature,
        status=TransactionStatus.FAILED if err else TransactionStatus.SUCCESS,
        slot=result.get("slot"),
        error=str(err) if err else None,
        logs=meta.get("logMessages", []),
        fee=meta.get("fee"),
        block_time=result.get("blockTime")
    )


def get_account_info(address: str, rpc_url: str = DEVNET_RPC) -> AccountInfo:
    """Get account information."""
    response = _rpc_call(
        "getAccountInfo",
        [address, {"encoding": "base64"}],
        rpc_url
    )
    
    if "error" in response:
        return AccountInfo(address=address, exists=False)
    
    result = response.get("result", {}).get("value")
    if result is None:
        return AccountInfo(address=address, exists=False)
    
    return AccountInfo(
        address=address,
        exists=True,
        lamports=result.get("lamports"),
        owner=result.get("owner"),
        executable=result.get("executable", False),
        data_len=len(result.get("data", [""])[0]) if result.get("data") else 0
    )


def get_recent_blockhash(rpc_url: str = DEVNET_RPC) -> Optional[str]:
    """Get recent blockhash (useful for checking RPC responsiveness)."""
    response = _rpc_call("getLatestBlockhash", [], rpc_url)
    
    if "error" in response:
        return None
    
    return response.get("result", {}).get("value", {}).get("blockhash")


def get_signatures_for_address(
    address: str, 
    limit: int = 10,
    rpc_url: str = DEVNET_RPC
) -> List[Dict]:
    """Get recent transaction signatures for an address."""
    response = _rpc_call(
        "getSignaturesForAddress",
        [address, {"limit": limit}],
        rpc_url
    )
    
    if "error" in response:
        return []
    
    return response.get("result", [])


def check_program_exists(program_id: str, rpc_url: str = DEVNET_RPC) -> bool:
    """Check if a program exists and is executable."""
    info = get_account_info(program_id, rpc_url)
    return info.exists and info.executable


# Convenience aliases
def devnet_health() -> RPCHealth:
    return check_rpc_health(DEVNET_RPC)

def mainnet_health() -> RPCHealth:
    return check_rpc_health(MAINNET_RPC)
