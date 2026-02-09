"""
AgentMedic Backup Manager
=========================
Manage agent state backups.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class BackupManager:
    """Manage state backups."""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, agent_id: str, state: Dict[str, Any]) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_id}_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        backup_data = {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state
        }
        
        with open(filepath, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return filepath
    
    def restore_backup(self, filepath: str) -> Optional[Dict[str, Any]]:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def list_backups(self, agent_id: str = None) -> list:
        backups = []
        for f in os.listdir(self.backup_dir):
            if f.endswith('.json'):
                if agent_id is None or f.startswith(agent_id):
                    backups.append(os.path.join(self.backup_dir, f))
        return sorted(backups, reverse=True)
    
    def get_latest(self, agent_id: str) -> Optional[str]:
        backups = self.list_backups(agent_id)
        return backups[0] if backups else None
    
    def cleanup(self, keep: int = 10):
        backups = self.list_backups()
        for backup in backups[keep:]:
            os.remove(backup)


_manager = None

def get_backup_manager(backup_dir: str = "./backups") -> BackupManager:
    global _manager
    if _manager is None:
        _manager = BackupManager(backup_dir)
    return _manager
