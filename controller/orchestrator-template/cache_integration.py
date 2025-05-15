import os
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import FileResponse
import openai
import time
import csv
import json
import tempfile
from cache_adapter import CacheAdapter

adapter = CacheAdapter()
cache_router = APIRouter(prefix="/cache", tags=["cache"])

class CacheStatsResponse(BaseModel):
    enabled: bool
    cache_size: Optional[int] = None
    hit_count: Optional[int] = None
    miss_count: Optional[int] = None
    hit_rate: Optional[float] = None
    total_saved_cost: Optional[float] = None
    status: Optional[str] = None

class CacheActionResponse(BaseModel):
    success: bool
    message: str
    current_state: Optional[bool] = None

class CacheEntryResponse(BaseModel):
    timestamp: str
    prompt: str
    similarity: float
    action: str

@cache_router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    return CacheStatsResponse(**adapter.get_stats())

@cache_router.post("/clear", response_model=CacheActionResponse)
async def clear_cache():
    adapter.clear_cache()
    return CacheActionResponse(success=True, message="Cache cleared")

@cache_router.post("/enable", response_model=CacheActionResponse)
async def enable_cache():
    result = adapter.set_enabled(True)
    return CacheActionResponse(**result)

@cache_router.post("/disable", response_model=CacheActionResponse)
async def disable_cache():
    result = adapter.set_enabled(False)
    return CacheActionResponse(**result)

@cache_router.get("/list", response_model=List[CacheEntryResponse])
async def list_cache_entries(limit: int = Query(10, ge=1, le=100)):
    return adapter.get_recent_entries(limit)

@cache_router.get("/export/json")
async def export_cache_json():
    entries = adapter.get_recent_entries(limit=1000)
    path = "logs/cache_export.json"
    os.makedirs("logs", exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)
    return FileResponse(path, filename="cache_export.json")

@cache_router.get("/export/csv")
async def export_cache_csv():
    entries = adapter.get_recent_entries(limit=1000)
    fieldnames = ["timestamp", "prompt", "similarity", "action"]
    path = "logs/cache_export.csv"
    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    return FileResponse(path, filename="cache_export.csv")

# New endpoint: Get similarity threshold
@cache_router.get("/threshold")
async def get_similarity_threshold():
    return {"threshold": adapter.get_threshold()}

# New endpoint: Set similarity threshold
@cache_router.post("/threshold")
async def set_similarity_threshold(threshold: float = Query(..., ge=0.0, le=1.0)):
    return adapter.set_threshold(threshold)

# New endpoint: Get TTL
@cache_router.get("/ttl")
async def get_ttl():
    return {"ttl_seconds": adapter.get_ttl()}

# New endpoint: Set TTL
@cache_router.post("/ttl")
async def set_ttl(ttl_seconds: int = Query(..., ge=60)):
    return adapter.set_ttl(ttl_seconds)


class LLMResponse:
    def __init__(self, response, model_used, latency, cost, input_tokens, output_tokens, selected_model):
        self.response = response
        self.model_used = model_used
        self.latency = latency
        self.cost = cost
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.selected_model = selected_model
      

async def openai_llm_call(prompt: str) -> LLMResponse:
    start = time.time()
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    end = time.time()
    content = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    cost = (input_tokens * 0.00000025) + (output_tokens * 0.00000125)
    return LLMResponse(
        response=content,
        model_used="gpt-3.5-turbo",
        latency=end - start,
        cost=cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        selected_model="gpt-3.5-turbo"
    )

def get_wrapped_llm_function():
    return adapter.wrap_llm_function(openai_llm_call)
