"""
AgentMedic Config Validator
===========================
Validate configuration for monitored agents.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"


class ConfigValidator:
    """Validate agent configurations."""
    
    REQUIRED_FIELDS = ["agent_id", "name"]
    OPTIONAL_FIELDS = ["process_name", "wallet_address", "rpc_endpoint", "alerts_enabled"]
    
    def validate(self, config: Dict[str, Any]) -> List[ValidationError]:
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in config or not config[field]:
                errors.append(ValidationError(field, f"Required field '{field}' is missing"))
        
        if "wallet_address" in config and config["wallet_address"]:
            if len(config["wallet_address"]) < 32:
                errors.append(ValidationError("wallet_address", "Invalid wallet address format", "warning"))
        
        if "rpc_endpoint" in config and config["rpc_endpoint"]:
            if not config["rpc_endpoint"].startswith(("http://", "https://")):
                errors.append(ValidationError("rpc_endpoint", "RPC endpoint must be a valid URL"))
        
        return errors
    
    def is_valid(self, config: Dict[str, Any]) -> bool:
        errors = self.validate(config)
        return not any(e.severity == "error" for e in errors)


def validate_config(config: Dict[str, Any]) -> tuple:
    validator = ConfigValidator()
    errors = validator.validate(config)
    return validator.is_valid(config), errors
