"""
Orchestrator Cache Integration - Integrates caching into the orchestrator
"""

import os
import sys
import json
import asyncio
import threading
import tkinter as tk
from typing import Dict, Any, Optional, Callable, Awaitable

# Import cache components
from cache_manager import get_cache_manager
from cache_gui import run_cache_gui

class OrchestratorCacheIntegration:
    """
    Integrates caching into the orchestrator.
    Provides methods for the orchestrator to interact with the cache.
    """
    
    def __init__(self, orchestrator_name="Orchestrator", cache_dir="../cache", enabled=True):
        """
        Initialize the orchestrator cache integration.
        
        Args:
            orchestrator_name: Name of the orchestrator
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled by default
        """
        self.orchestrator_name = orchestrator_name
        self.cache_dir = cache_dir
        self.enabled = enabled
        
        # Initialize cache manager
        self.cache_manager = get_cache_manager(cache_dir, enabled)
        
        # Initialize event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def open_cache_gui(self):
        """Open the cache GUI in a new thread"""
        run_cache_gui(self.orchestrator_name)

    
    def wrap_llm_function(self, llm_function: Callable[[str], str]):
        """
        Wrap an LLM function with caching.
        
        Args:
            llm_function: Function that takes a prompt and returns a response
            
        Returns:
            Wrapped function that checks cache before calling the LLM
        """
        return self.cache_manager.wrap_llm_function(llm_function)
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get the current cache status.
        
        Returns:
            Dict with cache status information
        """
        return {
            "enabled": self.cache_manager.adapter.enabled if self.cache_manager.adapter else False,
            "stats": self.cache_manager.get_stats()
        }
    
    def set_cache_enabled(self, enabled: bool) -> Dict[str, Any]:
        """
        Enable or disable the cache.
        
        Args:
            enabled: Whether to enable the cache
            
        Returns:
            Dict with result information
        """
        return self.cache_manager.set_enabled(enabled)
    
    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the cache.
        
        Returns:
            Dict with result information
        """
        return self.cache_manager.clear_cache()
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """
        Get the current cache settings.
        
        Returns:
            Dict with cache settings
        """
        return {
            "enabled": self.cache_manager.adapter.enabled if self.cache_manager.adapter else False,
            "threshold": self.cache_manager.get_threshold(),
            "ttl": self.cache_manager.get_ttl()
        }
    
    def set_cache_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set cache settings.
        
        Args:
            settings: Dict with cache settings
            
        Returns:
            Dict with result information
        """
        results = {}
        
        if "enabled" in settings:
            results["enabled"] = self.cache_manager.set_enabled(settings["enabled"])
        
        if "threshold" in settings:
            results["threshold"] = self.cache_manager.set_threshold(settings["threshold"])
        
        if "ttl" in settings:
            results["ttl"] = self.cache_manager.set_ttl(settings["ttl"])
        
        return results


# ✅ Factory method to get orchestrator integration
def get_cache_integration(orchestrator_name="Orchestrator", cache_dir="../cache", enabled=True):
    """
    Get the orchestrator cache integration instance.
    
    Args:
        orchestrator_name: Name of the orchestrator
        cache_dir: Directory to store cache files
        enabled: Whether caching is enabled by default
        
    Returns:
        OrchestratorCacheIntegration instance
    """
    return OrchestratorCacheIntegration(orchestrator_name, cache_dir, enabled)


# ✅ Optional CLI launch for testing GUI directly
def main():
    """
    Test this file directly: opens the GUI for manual use
    """
    orch = OrchestratorCacheIntegration(orchestrator_name="michelle", cache_dir="../cache", enabled=True)

    orch.open_cache_gui()

if __name__ == "__main__":
    main()
