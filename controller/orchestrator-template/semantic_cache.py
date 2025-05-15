import logging
import os
import json
from typing import Callable, Coroutine, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import hashlib
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic_cache")


class SemanticCache:
    def __init__(self, model_name="all-MiniLM-L6-v2", cache_path="./semantic_cache", enabled=True, ttl_seconds=3600):
        self.model_name = model_name
        self.cache_path = cache_path
        self.enabled = enabled
        self.logger = logger
        self.ttl_seconds = ttl_seconds  # ⏳ TTL in seconds (default 1 hour)

        self.cache = {}  # dict: hash -> {prompt, embedding, response, metadata, timestamp}
        self.index = None
        self.id_map = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saved_cost": 0.0,
        }

        os.makedirs(self.cache_path, exist_ok=True)
        self._init_model()
        self._load_cache()

    def _init_model(self):
        try:
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(self.dimension)
            self.logger.info(f"✅ Semantic cache initialized with model {self.model_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load embedding model: {e}")
            raise e

    def _get_embedding(self, prompt: str):
        return self.model.encode(prompt)

    def _hash_prompt(self, prompt: str):
        return hashlib.sha256(prompt.encode()).hexdigest()

    def _save_cache(self):
        with open(os.path.join(self.cache_path, "cache.json"), "w") as f:
            json.dump(self.cache, f, indent=2)
        faiss.write_index(self.index, os.path.join(self.cache_path, "index.faiss"))
        with open(os.path.join(self.cache_path, "stats.json"), "w") as f:
            json.dump(self.stats, f)
        self.logger.info(f"Saved cache with {len(self.cache)} entries")

    def _load_cache(self):
        try:
            data_file = os.path.join(self.cache_path, "cache.json")
            if os.path.exists(data_file):
                with open(data_file, "r") as f:
                    self.cache = json.load(f)

                embeddings = []
                for hash_key, item in self.cache.items():
                    embeddings.append(np.array(item["embedding"], dtype=np.float32))
                    self.id_map[len(self.id_map)] = hash_key

                if embeddings:
                    embeddings = np.vstack(embeddings).astype(np.float32)
                    self.index.add(embeddings)

                self.logger.info(f"Loaded {len(self.cache)} cached responses")
                self.logger.info(f"Loaded FAISS index with {self.index.ntotal} entries")

            stats_file = os.path.join(self.cache_path, "stats.json")
            if os.path.exists(stats_file):
                with open(stats_file, "r") as f:
                    self.stats = json.load(f)
                self.logger.info(f"Loaded stats: {self.stats['hits']} hits, {self.stats['misses']} misses")

        except Exception as e:
            self.logger.error(f"❌ Failed to load existing cache: {e}")

    def add(self, prompt: str, response: str):
        embedding = self._get_embedding(prompt)
        embedding_np = np.array([embedding]).astype(np.float32)

        hash_key = self._hash_prompt(prompt)
        self.cache[hash_key] = {
            "prompt": prompt,
            "embedding": embedding.tolist(),
            "response": response,
            "metadata": {},
            "timestamp": datetime.datetime.now().isoformat()  # ⏳ Add timestamp
        }

        self.index.add(embedding_np)
        self.id_map[self.index.ntotal - 1] = hash_key
        self._save_cache()

    def get_stats(self):
        hit_count = self.stats["hits"]
        miss_count = self.stats["misses"]
        total = hit_count + miss_count
        return {
            "enabled": self.enabled,
            "cache_size": len(self.cache),
            "hit_count": hit_count,
            "miss_count": miss_count,
            "hit_rate": round(hit_count / total, 4) if total > 0 else 0.0,
            "total_saved_cost": round(self.stats["saved_cost"], 6),
            "status": "✅ Semantic cache loaded and ready",
        }

    def clear(self):
        self.cache = {}
        self.index.reset()
        self.id_map = {}
        self.stats = {"hits": 0, "misses": 0, "saved_cost": 0.0}
        self._save_cache()

    def lookup(self, prompt: str):
        embedding = self._get_embedding(prompt)
        embedding_np = np.array([embedding]).astype(np.float32)

        if self.index.ntotal > 0:
            D, I = self.index.search(embedding_np, k=1)
            similarity = 1 / (1 + D[0][0])
            best_id = I[0][0]
            best_hash = self.id_map.get(best_id)

            if best_hash and best_hash in self.cache:
                cached = self.cache[best_hash]

                # ✅ Check for TTL expiration
                try:
                    ts = datetime.datetime.fromisoformat(cached.get("timestamp", "2000-01-01T00:00:00"))
                    if (datetime.datetime.now() - ts).total_seconds() > self.ttl_seconds:
                        self.logger.info(f"⏳ Cache entry expired (TTL hit): {prompt[:50]}...")
                        self.stats["misses"] += 1
                        return None
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to parse timestamp: {e}")

                if similarity >= 0.8:
                    self.stats["hits"] += 1
                    self.logger.info(f"✅ Cache hit! Similarity: {similarity:.4f}, Query: {prompt}...")
                    return {
                        "response": cached["response"],
                        "similarity": similarity,
                        "original_query": prompt,
                        "metadata": cached.get("metadata", {}),
                    }
                else:
                    self.logger.info(f"❌ Cache miss or low similarity ({similarity:.4f}) for: {prompt}...")

        self.logger.info(f"❌ Cache miss for: {prompt}")
        self.stats["misses"] += 1
        return None

    def wrap_async(self, func: Callable[[str], Coroutine[Any, Any, Any]]) -> Callable[[str], Coroutine[Any, Any, Any]]:
        async def wrapped(prompt: str):
            if not self.enabled:
                return await func(prompt)

            result = self.lookup(prompt)
            if result and result.get("similarity", 0) >= 0.8:
                return result

            response = await func(prompt)
            self.stats["misses"] += 1
            self.stats["saved_cost"] += getattr(response, "cost", 0)

            hash_key = self._hash_prompt(prompt)
            embedding = self._get_embedding(prompt)

            self.cache[hash_key] = {
                "prompt": prompt,
                "embedding": embedding.tolist(),
                "response": response.response if hasattr(response, "response") else response,
                "metadata": {},
                "timestamp": datetime.datetime.now().isoformat()
            }

            self.index.add(np.array([embedding]).astype(np.float32))
            self.id_map[self.index.ntotal - 1] = hash_key
            self._save_cache()

            return {
                "response": response.response if hasattr(response, "response") else response,
                "similarity": None,
                "original_query": prompt,
                "metadata": {},
            }

        return wrapped


def get_semantic_cache():
    return SemanticCache()
