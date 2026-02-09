"""
AgentMedic State Machine
========================
Finite state machine for agent lifecycle.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum


class AgentState(Enum):
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    FAILED = "failed"
    STOPPED = "stopped"


VALID_TRANSITIONS = {
    AgentState.UNKNOWN: [AgentState.STARTING, AgentState.HEALTHY, AgentState.FAILED],
    AgentState.STARTING: [AgentState.HEALTHY, AgentState.FAILED],
    AgentState.HEALTHY: [AgentState.DEGRADED, AgentState.FAILED, AgentState.STOPPED],
    AgentState.DEGRADED: [AgentState.HEALTHY, AgentState.RECOVERING, AgentState.FAILED],
    AgentState.RECOVERING: [AgentState.HEALTHY, AgentState.DEGRADED, AgentState.FAILED],
    AgentState.FAILED: [AgentState.RECOVERING, AgentState.STOPPED],
    AgentState.STOPPED: [AgentState.STARTING],
}


class StateMachine:
    """Agent state machine."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state = AgentState.UNKNOWN
        self.history: List[tuple] = []
        self._callbacks: Dict[AgentState, List[Callable]] = {}
    
    def can_transition(self, new_state: AgentState) -> bool:
        return new_state in VALID_TRANSITIONS.get(self.state, [])
    
    def transition(self, new_state: AgentState) -> bool:
        if not self.can_transition(new_state):
            return False
        
        old_state = self.state
        self.state = new_state
        self.history.append((old_state, new_state))
        
        for cb in self._callbacks.get(new_state, []):
            try:
                cb(self.agent_id, old_state, new_state)
            except:
                pass
        
        return True
    
    def on_enter(self, state: AgentState, callback: Callable):
        if state not in self._callbacks:
            self._callbacks[state] = []
        self._callbacks[state].append(callback)


_machines: Dict[str, StateMachine] = {}

def get_state_machine(agent_id: str) -> StateMachine:
    if agent_id not in _machines:
        _machines[agent_id] = StateMachine(agent_id)
    return _machines[agent_id]
