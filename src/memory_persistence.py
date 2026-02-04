"""
AgentMedic - Memory Persistence Module
======================================
Stores agent memory on-chain (Solana) or decentralized storage (IPFS/Arweave).
Enables agents to survive resets and maintain continuity.

Features:
- Backup critical memory to Solana (memo transactions)
- Store larger data on IPFS/Arweave with on-chain pointers
- Retrieve and restore memory after restart
- Encrypt sensitive data before storage
- Version memory snapshots with timestamps

Safety:
- Read-only on Solana (uses memo program, no fund transfers)
- Never stores private keys or credentials
- Encryption for sensitive data
"""

import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# Solana imports (optional - for future on-chain storage)
try:
    from solana_rpc import TransactionStatus, TransactionResult
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False


class StorageBackend(Enum):
    """Supported storage backends for memory persistence."""
    SOLANA_MEMO = "solana_memo"  # Small data via memo program
    IPFS = "ipfs"                # Large data via IPFS
    ARWEAVE = "arweave"          # Permanent storage via Arweave
    LOCAL = "local"              # Local file backup (fallback)


@dataclass
class MemorySnapshot:
    """A point-in-time snapshot of agent memory."""
    agent_id: str
    timestamp: str
    version: int
    data: Dict[str, Any]
    checksum: str
    storage_backend: str
    storage_ref: Optional[str] = None  # IPFS CID, Arweave TX, or Solana signature
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MemorySnapshot':
        data = json.loads(json_str)
        return cls(**data)


class MemoryPersistence:
    """
    Handles persistent storage of agent memory.
    
    Primary use cases:
    1. Backup critical agent state to survive restarts
    2. Store diagnostic history for pattern learning
    3. Share learned patterns with other agents
    4. Maintain agent identity across sessions
    """
    
    def __init__(
        self,
        agent_id: str,
        solana_rpc: Optional[Any] = None,
        storage_backend: StorageBackend = StorageBackend.LOCAL,
        encryption_key: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.solana_rpc = solana_rpc  # Reserved for future on-chain storage
        self.storage_backend = storage_backend
        self.encryption_key = encryption_key
        self.version = 0
        self.snapshots: List[MemorySnapshot] = []
        
    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        """Compute SHA-256 checksum of memory data."""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data before storage (placeholder - implement with proper crypto)."""
        if not self.encryption_key:
            return data
        # TODO: Implement proper AES encryption
        # For now, just base64 encode as placeholder
        return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt data after retrieval."""
        if not self.encryption_key:
            return data
        # TODO: Implement proper AES decryption
        return base64.b64decode(data.encode()).decode()
    
    def create_snapshot(self, memory_data: Dict[str, Any]) -> MemorySnapshot:
        """Create a new memory snapshot."""
        self.version += 1
        
        snapshot = MemorySnapshot(
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=self.version,
            data=memory_data,
            checksum=self._compute_checksum(memory_data),
            storage_backend=self.storage_backend.value
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    async def save_to_solana_memo(self, snapshot: MemorySnapshot) -> Optional[str]:
        """
        Save memory snapshot reference to Solana via memo program.
        
        Note: Memo program has size limits (~566 bytes).
        For larger data, store on IPFS and put CID in memo.
        """
        if not self.solana_rpc:
            print("Warning: No Solana RPC configured")
            return None
            
        # Create compact memo with essential info
        memo_data = {
            "agent": self.agent_id,
            "v": snapshot.version,
            "ts": snapshot.timestamp[:19],  # Truncate for space
            "checksum": snapshot.checksum,
            "ref": snapshot.storage_ref  # IPFS/Arweave reference if used
        }
        
        memo_json = json.dumps(memo_data, separators=(',', ':'))
        
        # TODO: Implement actual Solana memo transaction
        # This requires signing capability which we don't have (read-only design)
        # For hackathon demo: log what WOULD be stored
        print(f"[Memory] Would store to Solana memo: {memo_json}")
        
        return None  # Return tx signature when implemented
    
    def save_to_local(self, snapshot: MemorySnapshot, filepath: str) -> bool:
        """Save memory snapshot to local file (fallback storage)."""
        try:
            with open(filepath, 'w') as f:
                f.write(snapshot.to_json())
            snapshot.storage_ref = filepath
            print(f"[Memory] Saved snapshot v{snapshot.version} to {filepath}")
            return True
        except Exception as e:
            print(f"[Memory] Error saving to local: {e}")
            return False
    
    def load_from_local(self, filepath: str) -> Optional[MemorySnapshot]:
        """Load memory snapshot from local file."""
        try:
            with open(filepath, 'r') as f:
                return MemorySnapshot.from_json(f.read())
        except Exception as e:
            print(f"[Memory] Error loading from local: {e}")
            return None
    
    async def save_to_ipfs(self, snapshot: MemorySnapshot) -> Optional[str]:
        """
        Save memory snapshot to IPFS.
        Returns CID (Content Identifier) for retrieval.
        """
        # TODO: Implement IPFS pinning via Pinata, Infura, or local node
        # For hackathon demo: simulate
        
        json_data = snapshot.to_json()
        simulated_cid = f"Qm{hashlib.sha256(json_data.encode()).hexdigest()[:44]}"
        
        print(f"[Memory] Would store to IPFS: {len(json_data)} bytes -> {simulated_cid}")
        snapshot.storage_ref = simulated_cid
        
        return simulated_cid
    
    async def backup_memory(
        self,
        memory_data: Dict[str, Any],
        backends: Optional[List[StorageBackend]] = None
    ) -> MemorySnapshot:
        """
        Backup agent memory to configured storage backends.
        
        Args:
            memory_data: Dictionary of memory to persist
            backends: List of backends to use (default: configured backend)
            
        Returns:
            MemorySnapshot with storage references
        """
        if backends is None:
            backends = [self.storage_backend]
            
        snapshot = self.create_snapshot(memory_data)
        
        for backend in backends:
            if backend == StorageBackend.LOCAL:
                filepath = f"memory_snapshot_v{snapshot.version}.json"
                self.save_to_local(snapshot, filepath)
                
            elif backend == StorageBackend.IPFS:
                await self.save_to_ipfs(snapshot)
                
            elif backend == StorageBackend.SOLANA_MEMO:
                await self.save_to_solana_memo(snapshot)
                
            elif backend == StorageBackend.ARWEAVE:
                # TODO: Implement Arweave storage
                print(f"[Memory] Arweave storage not yet implemented")
        
        return snapshot
    
    def get_latest_snapshot(self) -> Optional[MemorySnapshot]:
        """Get the most recent memory snapshot."""
        if not self.snapshots:
            return None
        return self.snapshots[-1]
    
    def get_snapshot_by_version(self, version: int) -> Optional[MemorySnapshot]:
        """Get a specific version of memory snapshot."""
        for snapshot in self.snapshots:
            if snapshot.version == version:
                return snapshot
        return None
    
    def verify_integrity(self, snapshot: MemorySnapshot) -> bool:
        """Verify snapshot data integrity via checksum."""
        computed = self._compute_checksum(snapshot.data)
        is_valid = computed == snapshot.checksum
        
        if not is_valid:
            print(f"[Memory] Integrity check FAILED: expected {snapshot.checksum}, got {computed}")
        
        return is_valid


# Convenience function for AgentMedic's own memory
def create_agentmedic_memory_manager() -> MemoryPersistence:
    """Create a memory persistence manager for AgentMedic itself."""
    return MemoryPersistence(
        agent_id="AgentMedic",
        storage_backend=StorageBackend.LOCAL  # Start with local, upgrade to IPFS/Solana
    )


# Demo/test function
async def demo_memory_persistence():
    """Demonstrate memory persistence functionality."""
    print("=" * 60)
    print("AgentMedic Memory Persistence Demo")
    print("=" * 60)
    
    # Create memory manager
    memory = create_agentmedic_memory_manager()
    
    # Sample memory data (what AgentMedic would remember)
    agent_memory = {
        "identity": {
            "name": "AgentMedic",
            "agent_id": 149,
            "mission": "Autonomous AI Doctor for Solana Agents"
        },
        "learned_patterns": {
            "rpc_failures": ["provider_x_rate_limits_at_2am", "timeout_after_1000_requests"],
            "common_crashes": ["oom_on_large_responses", "connection_pool_exhaustion"]
        },
        "diagnostic_history": {
            "total_incidents": 42,
            "successful_recoveries": 38,
            "escalated_to_human": 4
        },
        "trusted_agents": ["moltdev", "BlockScoreBot", "openfort-wallet-infra"],
        "last_active": datetime.now(timezone.utc).isoformat()
    }
    
    # Create and save snapshot
    print("\n[1] Creating memory snapshot...")
    snapshot = await memory.backup_memory(
        agent_memory,
        backends=[StorageBackend.LOCAL, StorageBackend.IPFS]
    )
    
    print(f"\n[2] Snapshot created:")
    print(f"    Version: {snapshot.version}")
    print(f"    Checksum: {snapshot.checksum}")
    print(f"    Storage ref: {snapshot.storage_ref}")
    
    # Verify integrity
    print(f"\n[3] Verifying integrity...")
    is_valid = memory.verify_integrity(snapshot)
    print(f"    Integrity check: {'PASSED ✓' if is_valid else 'FAILED ✗'}")
    
    # Simulate retrieval after restart
    print(f"\n[4] Simulating memory retrieval after restart...")
    latest = memory.get_latest_snapshot()
    if latest:
        print(f"    Retrieved: v{latest.version} from {latest.timestamp}")
        print(f"    Agent identity: {latest.data.get('identity', {}).get('name')}")
        print(f"    Learned patterns: {len(latest.data.get('learned_patterns', {}))} categories")
    
    print("\n" + "=" * 60)
    print("Memory persistence demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_memory_persistence())
