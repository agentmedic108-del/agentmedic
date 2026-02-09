"""
AgentMedic Task Scheduler
=========================
Schedule and manage periodic tasks.
"""

import time
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Optional


@dataclass
class Task:
    name: str
    callback: Callable
    interval_seconds: float
    last_run: Optional[datetime] = None
    enabled: bool = True


class Scheduler:
    """Simple task scheduler."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def add_task(self, name: str, callback: Callable, interval_seconds: float):
        self.tasks[name] = Task(name=name, callback=callback, interval_seconds=interval_seconds)
    
    def remove_task(self, name: str):
        self.tasks.pop(name, None)
    
    def _should_run(self, task: Task) -> bool:
        if not task.enabled:
            return False
        if task.last_run is None:
            return True
        elapsed = (datetime.now(timezone.utc) - task.last_run).total_seconds()
        return elapsed >= task.interval_seconds
    
    def _run_loop(self):
        while self._running:
            for task in list(self.tasks.values()):
                if self._should_run(task):
                    try:
                        task.callback()
                        task.last_run = datetime.now(timezone.utc)
                    except Exception as e:
                        print(f"Task {task.name} error: {e}")
            time.sleep(1)
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


_scheduler = None

def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
