import os
import json
import datetime
import logging
from typing import Dict, Any, Callable
from semantic_cache import SemanticCache  # Our core semantic cache engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cache_adapter")

class CacheAdapter:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "./semantic_cache", enabled: bool = True, ttl_seconds: int = 3600):
        self.enabled = enabled
        self.cache = None
        if enabled:
            try:
                self.cache = SemanticCache(
                    model_name=model_name,
                    cache_path=cache_dir,
                    enabled=enabled,
                    ttl_seconds=ttl_seconds
                )
                logger.info(f"■ Semantic cache initialized with model {model_name}")
            except Exception as e:
                logger.error(f"■ Failed to initialize semantic cache: {e}")
                self.enabled = False

    def wrap_llm_function(self, llm_function: Callable) -> Callable:
        # Wrap an async LLM function with semantic caching
        async def wrapped_function(prompt: str, *args, **kwargs):
            if not self.enabled or self.cache is None:
                return await llm_function(prompt, *args, **kwargs)

            cache_result = self.cache.lookup(prompt)
            similarity = cache_result.get("similarity") if cache_result else 0.0

            if cache_result and cache_result.get("response"):
                self._log_history(prompt, similarity, "HIT")
                return self._wrap_cached_response(cache_result["response"], similarity, "HIT")

            # Cache miss or too low similarity
            result = await llm_function(prompt, *args, **kwargs)

            # Add metadata
            result.cache_status = "MISS"
            result.similarity = similarity  # Preserve actual similarity even on miss

            response_text = None
            metadata = {}
            if hasattr(result, 'response') and isinstance(result.response, str):
                response_text = result.response
                for attr in ['model_used', 'latency', 'cost', 'input_tokens', 'output_tokens', 'selected_model']:
                    if hasattr(result, attr):
                        metadata[attr] = getattr(result, attr)
            elif isinstance(result, str):
                response_text = result
            else:
                response_text = str(result)

            if response_text and self._is_valid_prompt(prompt):
                self.cache.add(prompt, response_text)
                self._log_history(prompt, 1.0, "STORE")
                return self._wrap_cached_response(response_text, similarity=1.0, action="STORE")
            else:
                logger.info(f"Skipped caching junk prompt: {prompt}")
                return result

        return wrapped_function

    def _wrap_cached_response(self, response_text: str, similarity: float = 1.0, action: str = "HIT"):
        from types import SimpleNamespace
        return SimpleNamespace(
            response=response_text,
            model_used="Cached",
            latency=0,
            cost=0,
            input_tokens=0,
            output_tokens=0,
            selected_model="Cached",
            similarity=similarity,
            cache_status=action
        )

    def _is_valid_prompt(self, prompt: str) -> bool:
        if not prompt.strip():
            return False
        words = prompt.strip().split()
        if len(words) < 3:
            return False
        junk_words = ["hi", "hello", "test", "ok", "okay", "hmm", "huh", "hiii", "hlo"]
        if all(word.lower() in junk_words for word in words):
            return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        if not self.enabled or self.cache is None:
            return {'enabled': False, 'status': 'Cache disabled'}
        stats = self.cache.get_stats()
        stats['enabled'] = True
        return stats

    def clear_cache(self) -> Dict[str, Any]:
        if not self.enabled or self.cache is None:
            return {'success': False, 'message': 'Cache is not enabled'}
        self.cache.clear()
        self._log_history("N/A", 0.0, "CLEAR")
        return {'success': True, 'message': 'Cache cleared successfully'}

    def set_enabled(self, enabled: bool) -> Dict[str, Any]:
        old_state = self.enabled
        self.enabled = enabled
        return {
            'success': True,
            'previous_state': old_state,
            'current_state': self.enabled,
            'message': f"Cache {'enabled' if enabled else 'disabled'}"
        }

    def get_recent_entries(self, limit: int = 10) -> list:
        log_path = "logs/cache_list.log"
        if not os.path.exists(log_path):
            return []
        with open(log_path, "r") as f:
            lines = f.readlines()
            entries = [json.loads(line.strip()) for line in lines[-limit:] if line.strip()]
            return entries

    def get_threshold(self) -> float:
        if self.cache and hasattr(self.cache, "similarity_threshold"):
            return self.cache.similarity_threshold
        return 0.8

    def set_threshold(self, threshold: float) -> Dict[str, Any]:
        if not self.cache:
            return {'success': False, 'message': 'Cache not initialized'}
        self.cache.similarity_threshold = threshold  # ✅ This makes threshold dynamic
        return {'success': True, 'message': f"Threshold updated to {threshold}"}

    def get_ttl(self) -> int:
        if self.cache and hasattr(self.cache, "ttl_seconds"):
            return self.cache.ttl_seconds
        return 3600

    def set_ttl(self, ttl_seconds: int) -> Dict[str, Any]:
        if not self.cache:
            return {'success': False, 'message': 'Cache not initialized'}
        self.cache.ttl_seconds = ttl_seconds
        return {'success': True, 'message': f"TTL updated to {ttl_seconds} seconds"}

    def _log_history(self, prompt: str, similarity: float, action: str):
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "prompt": prompt,
            "similarity": round(similarity, 4),
            "action": action
        }
        with open("logs/cache_history.log", "a") as f:
            f.write(f"{timestamp} - {action} - Sim: {entry['similarity']} - Prompt: {prompt[:100]}\n")
        with open("logs/cache_list.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
