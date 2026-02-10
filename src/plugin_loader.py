"""
AgentMedic Plugin Loader
========================
Dynamic plugin loading system.
"""

import importlib
import os
from typing import Dict, Any, Optional, Protocol


class Plugin(Protocol):
    name: str
    version: str
    def initialize(self) -> None: ...
    def shutdown(self) -> None: ...


class PluginLoader:
    """Load and manage plugins."""
    
    def __init__(self, plugin_dir: str = "./plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Any] = {}
    
    def discover(self) -> list:
        if not os.path.exists(self.plugin_dir):
            return []
        
        plugins = []
        for item in os.listdir(self.plugin_dir):
            if item.endswith('.py') and not item.startswith('_'):
                plugins.append(item[:-3])
        return plugins
    
    def load(self, plugin_name: str) -> bool:
        try:
            module = importlib.import_module(f"plugins.{plugin_name}")
            if hasattr(module, 'initialize'):
                module.initialize()
            self.plugins[plugin_name] = module
            return True
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload(self, plugin_name: str) -> bool:
        if plugin_name not in self.plugins:
            return False
        
        module = self.plugins[plugin_name]
        if hasattr(module, 'shutdown'):
            module.shutdown()
        
        del self.plugins[plugin_name]
        return True
    
    def load_all(self) -> int:
        loaded = 0
        for plugin in self.discover():
            if self.load(plugin):
                loaded += 1
        return loaded
    
    def get_plugin(self, name: str) -> Optional[Any]:
        return self.plugins.get(name)


_loader = None

def get_plugin_loader(plugin_dir: str = "./plugins") -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader(plugin_dir)
    return _loader
