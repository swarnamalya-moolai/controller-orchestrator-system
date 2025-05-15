"""
Cache Manager - Plug-and-play integration for semantic caching
This file integrates semantic_cache.py, cache_adapter.py, and cache_integration.py
"""

import os
import sys
import json
import importlib.util
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cache_manager")

class CacheManager:
    """
    Manages the integration between the orchestrator and the caching system.
    Acts as a facade for the semantic cache, adapter, and integration components.
    """
    
    def __init__(self, cache_dir: str = "./cache", enabled: bool = True):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled by default
        """
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.adapter = None
        self.integration = None
        self.semantic_cache = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load configuration if it exists
        self.config = self._load_config()
        
        # Initialize components
        self._init_components()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load cache configuration from file"""
        config_path = os.path.join(self.cache_dir, "cache_config.json")
        default_config = {
            "enabled": self.enabled,
            "threshold": 0.8,
            "ttl_seconds": 3600,
            "model_name": "all-MiniLM-L6-v2"
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                logger.info(f"Loaded cache configuration from {config_path}")
                return {**default_config, **config}  # Merge with defaults
            except Exception as e:
                logger.error(f"Error loading cache configuration: {e}")
        
        # Save default config
        try:
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving default configuration: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file"""
        config_path = os.path.join(self.cache_dir, "cache_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved cache configuration to {config_path}")
        except Exception as e:
            logger.error(f"Error saving cache configuration: {e}")
    
    def _init_components(self):
        """Initialize cache components"""
        try:
            # Import the modules dynamically
            cache_modules = self._import_cache_modules()
            
            if not cache_modules:
                logger.error("Failed to import cache modules")
                return
            
            # Extract the modules
            semantic_cache_module = cache_modules.get("semantic_cache")
            cache_adapter_module = cache_modules.get("cache_adapter")
            cache_integration_module = cache_modules.get("cache_integration")
            
            if semantic_cache_module:
                self.semantic_cache = semantic_cache_module.SemanticCache(
                    model_name=self.config.get("model_name", "all-MiniLM-L6-v2"),
                    cache_path=os.path.join(self.cache_dir, "semantic_cache"),
                    enabled=self.config.get("enabled", True),
                    ttl_seconds=self.config.get("ttl_seconds", 3600)
                )
                logger.info("Initialized semantic cache")
            
            if cache_adapter_module:
                # If we have our own semantic cache instance, use it
                if self.semantic_cache:
                    self.adapter = cache_adapter_module.CacheAdapter(
                        model_name=self.config.get("model_name", "all-MiniLM-L6-v2"),
                        cache_dir=os.path.join(self.cache_dir, "semantic_cache"),
                        enabled=self.config.get("enabled", True),
                        ttl_seconds=self.config.get("ttl_seconds", 3600)
                    )
                    # Replace the adapter's cache with our instance
                    self.adapter.cache = self.semantic_cache
                else:
                    # Otherwise create a new adapter
                    self.adapter = cache_adapter_module.CacheAdapter(
                        model_name=self.config.get("model_name", "all-MiniLM-L6-v2"),
                        cache_dir=os.path.join(self.cache_dir, "semantic_cache"),
                        enabled=self.config.get("enabled", True),
                        ttl_seconds=self.config.get("ttl_seconds", 3600)
                    )
                logger.info("Initialized cache adapter")
            
            if cache_integration_module:
                # Store the module for API integration
                self.integration = cache_integration_module
                logger.info("Loaded cache integration module")
            
        except Exception as e:
            logger.error(f"Error initializing cache components: {e}")
    
    def _import_cache_modules(self):
        """Dynamically import the cache modules"""
        modules = {}
        
        # List of modules to import
        module_paths = {
            "semantic_cache": "semantic_cache.py",
            "cache_adapter": "cache_adapter.py",
            "cache_integration": "cache_integration.py"
        }
        
        # Check current directory first, then check if modules are in the path
        for module_name, file_name in module_paths.items():
            # Try local file first
            if os.path.exists(file_name):
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_name)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    modules[module_name] = module
                    logger.info(f"Imported {module_name} from {file_name}")
                    continue
                except Exception as e:
                    logger.warning(f"Error importing {module_name} from file: {e}")
            
            # Try importing from path
            try:
                module = importlib.import_module(module_name)
                modules[module_name] = module
                logger.info(f"Imported {module_name} from path")
            except ImportError:
                logger.warning(f"Could not import {module_name}")
        
        return modules
    
    def wrap_llm_function(self, llm_function):
        """
        Wrap an LLM function with caching.
        
        Args:
            llm_function: Async function that takes a prompt and returns a response
            
        Returns:
            Wrapped function that checks cache before calling the LLM
        """
        if not self.adapter:
            logger.warning("Cache adapter not initialized, returning original function")
            return llm_function
        
        return self.adapter.wrap_llm_function(llm_function)
    
    def get_stats(self):
        """Get cache statistics"""
        if not self.adapter:
            return {'enabled': False, 'status': 'Cache not initialized'}
        
        return self.adapter.get_stats()
    
    def clear_cache(self):
        """Clear the cache"""
        if not self.adapter:
            return {'success': False, 'message': 'Cache not initialized'}
        
        return self.adapter.clear_cache()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the cache"""
        if not self.adapter:
            return {'success': False, 'message': 'Cache not initialized'}
        
        result = self.adapter.set_enabled(enabled)
        
        # Update config
        self.config["enabled"] = enabled
        self._save_config()
        
        return result
    
    def get_threshold(self):
        """Get the similarity threshold"""
        if not self.adapter:
            return 0.8
        
        return self.adapter.get_threshold()
    
    def set_threshold(self, threshold: float):
        """Set the similarity threshold"""
        if not self.adapter:
            return {'success': False, 'message': 'Cache not initialized'}
        
        result = self.adapter.set_threshold(threshold)
        
        # Update config
        self.config["threshold"] = threshold
        self._save_config()
        
        return result
    
    def get_ttl(self):
        """Get the TTL in seconds"""
        if not self.adapter:
            return 3600
        
        return self.adapter.get_ttl()
    
    def set_ttl(self, ttl_seconds: int):
        """Set the TTL in seconds"""
        if not self.adapter:
            return {'success': False, 'message': 'Cache not initialized'}
        
        result = self.adapter.set_ttl(ttl_seconds)
        
        # Update config
        self.config["ttl_seconds"] = ttl_seconds
        self._save_config()
        
        return result
    
    def get_recent_entries(self, limit: int = 10):
        """Get recent cache entries"""
        if not self.adapter:
            return []
        
        return self.adapter.get_recent_entries(limit)
    
    def lookup(self, prompt: str):
        """
        Look up a prompt in the cache.
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Cache result or None if not found
        """
        if not self.semantic_cache:
            return None
        
        return self.semantic_cache.lookup(prompt)
    
    def add(self, prompt: str, response: str):
        """
        Add a prompt-response pair to the cache.
        
        Args:
            prompt: The prompt
            response: The response
        """
        if not self.semantic_cache:
            return
        
        self.semantic_cache.add(prompt, response)

# Singleton instance
_cache_manager = None

def get_cache_manager(cache_dir: str = "./cache", enabled: bool = True):
    """
    Get the singleton cache manager instance.
    
    Args:
        cache_dir: Directory to store cache files
        enabled: Whether caching is enabled by default
        
    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, enabled)
    return _cache_manager
