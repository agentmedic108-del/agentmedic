"""
Tests for Memory Persistence Module
"""

import pytest
import asyncio
import json
import os
from datetime import datetime, timezone

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_persistence import (
    MemoryPersistence,
    MemorySnapshot,
    StorageBackend,
    create_agentmedic_memory_manager
)


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass"""
    
    def test_snapshot_creation(self):
        snapshot = MemorySnapshot(
            agent_id="test-agent",
            timestamp="2026-02-04T12:00:00Z",
            version=1,
            data={"key": "value"},
            checksum="abc123",
            storage_backend="local"
        )
        assert snapshot.agent_id == "test-agent"
        assert snapshot.version == 1
        assert snapshot.data["key"] == "value"
    
    def test_snapshot_json_roundtrip(self):
        snapshot = MemorySnapshot(
            agent_id="test-agent",
            timestamp="2026-02-04T12:00:00Z",
            version=1,
            data={"nested": {"key": "value"}},
            checksum="abc123",
            storage_backend="local"
        )
        json_str = snapshot.to_json()
        restored = MemorySnapshot.from_json(json_str)
        assert restored.agent_id == snapshot.agent_id
        assert restored.data == snapshot.data


class TestMemoryPersistence:
    """Test MemoryPersistence class"""
    
    def test_create_manager(self):
        manager = MemoryPersistence(
            agent_id="test-agent",
            storage_backend=StorageBackend.LOCAL
        )
        assert manager.agent_id == "test-agent"
        assert manager.version == 0
    
    def test_checksum_computation(self):
        manager = MemoryPersistence(agent_id="test")
        data = {"key": "value"}
        checksum = manager._compute_checksum(data)
        assert len(checksum) == 16  # SHA-256 truncated to 16 chars
        
        # Same data = same checksum
        checksum2 = manager._compute_checksum(data)
        assert checksum == checksum2
        
        # Different data = different checksum
        checksum3 = manager._compute_checksum({"key": "different"})
        assert checksum != checksum3
    
    def test_create_snapshot(self):
        manager = MemoryPersistence(agent_id="test")
        snapshot = manager.create_snapshot({"memory": "data"})
        
        assert snapshot.version == 1
        assert snapshot.agent_id == "test"
        assert snapshot.data == {"memory": "data"}
        assert len(snapshot.checksum) == 16
    
    def test_version_increments(self):
        manager = MemoryPersistence(agent_id="test")
        s1 = manager.create_snapshot({"v": 1})
        s2 = manager.create_snapshot({"v": 2})
        s3 = manager.create_snapshot({"v": 3})
        
        assert s1.version == 1
        assert s2.version == 2
        assert s3.version == 3
    
    def test_integrity_verification(self):
        manager = MemoryPersistence(agent_id="test")
        snapshot = manager.create_snapshot({"important": "data"})
        
        # Valid snapshot passes
        assert manager.verify_integrity(snapshot) == True
        
        # Tampered data fails
        snapshot.data["important"] = "tampered"
        assert manager.verify_integrity(snapshot) == False
    
    def test_get_latest_snapshot(self):
        manager = MemoryPersistence(agent_id="test")
        
        assert manager.get_latest_snapshot() is None
        
        manager.create_snapshot({"v": 1})
        manager.create_snapshot({"v": 2})
        latest = manager.create_snapshot({"v": 3})
        
        assert manager.get_latest_snapshot() == latest
    
    def test_get_snapshot_by_version(self):
        manager = MemoryPersistence(agent_id="test")
        s1 = manager.create_snapshot({"v": 1})
        s2 = manager.create_snapshot({"v": 2})
        
        assert manager.get_snapshot_by_version(1) == s1
        assert manager.get_snapshot_by_version(2) == s2
        assert manager.get_snapshot_by_version(99) is None


class TestAgentMedicMemoryManager:
    """Test convenience function"""
    
    def test_create_agentmedic_manager(self):
        manager = create_agentmedic_memory_manager()
        assert manager.agent_id == "AgentMedic"
        assert manager.storage_backend == StorageBackend.LOCAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
