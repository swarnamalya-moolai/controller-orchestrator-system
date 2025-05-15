from flask import Blueprint, request, jsonify
from cache_adapter import CacheAdapter

cache_bp = Blueprint('cache_bp', __name__)
adapter = CacheAdapter()

@cache_bp.route("/api/cache/<orchestrator_id>/toggle", methods=["POST"])
def toggle_cache(orchestrator_id):
    current = adapter.enabled
    adapter.set_enabled(not current)
    return jsonify({"status": "ok", "cache_enabled": adapter.enabled})

@cache_bp.route("/api/cache/<orchestrator_id>/settings", methods=["POST"])
def update_cache_settings(orchestrator_id):
    data = request.json
    response = {"status": "ok"}

    if "enabled" in data:
        adapter.set_enabled(data["enabled"])
        response["cache_enabled"] = data["enabled"]

    if "ttl" in data:
        adapter.set_ttl(int(data["ttl"]))

    if "threshold" in data:
        adapter.set_threshold(float(data["threshold"]))

    return jsonify(response)

@cache_bp.route("/api/cache/<orchestrator_id>/stats", methods=["GET"])
def get_stats(orchestrator_id):
    stats = adapter.get_stats()
    return jsonify({"status": "ok", "stats": stats})
