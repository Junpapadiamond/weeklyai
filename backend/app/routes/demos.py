"""Interactive demo API.

    GET  /api/v1/demos/status               provider + coverage
    GET  /api/v1/demos                      products that already have a demo
    GET  /api/v1/demos/<product_id>         fetch a demo (cached)
    POST /api/v1/demos/<product_id>/generate  build one now
    POST /api/v1/demos/live                 proxy one approved sandbox call

Generation costs money and time, so it carries its own hourly per-IP budget on
top of the global limiter.
"""
from __future__ import annotations

from collections import defaultdict
import time

from flask import Blueprint, jsonify, request

from app.services.demo_repository import DemoRepository
from app.services.demo_spec import ENDPOINT_REGISTRY
from app.services import demo_service

demos_bp = Blueprint("demos", __name__)

GENERATE_LIMIT_PER_HOUR = 8
LIVE_LIMIT_PER_MINUTE = 12

_generate_tracker: dict[str, list[float]] = defaultdict(list)
_live_tracker: dict[str, list[float]] = defaultdict(list)


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    return forwarded.split(",")[0].strip()


def _allow(tracker: dict[str, list[float]], ip: str, limit: int, window: int) -> bool:
    now = time.time()
    tracker[ip] = [t for t in tracker[ip] if t > now - window]
    if len(tracker[ip]) >= limit:
        return False
    tracker[ip].append(now)
    return True


def _find_product(product_id: str):
    from app.services.product_service import ProductService
    return ProductService.get_product_by_id(product_id)


@demos_bp.route("/status", methods=["GET"])
def status():
    slugs = DemoRepository.list_slugs()
    return jsonify({
        "success": True,
        "generation_available": demo_service.is_configured(),
        "live_endpoints": sorted(ENDPOINT_REGISTRY),
        "demo_count": len(slugs),
        "generate_limit_per_hour": GENERATE_LIMIT_PER_HOUR,
    })


@demos_bp.route("", methods=["GET"])
def list_demos():
    """Slugs we can serve immediately. The picker uses this to mark products
    as instant rather than generate-on-demand."""
    return jsonify({"success": True, "data": DemoRepository.list_slugs()})


@demos_bp.route("/<path:product_id>/generate", methods=["POST"])
def generate_demo(product_id):
    ip = _client_ip()
    if not _allow(_generate_tracker, ip, GENERATE_LIMIT_PER_HOUR, 3600):
        return jsonify({
            "success": False,
            "error": "TOO_MANY_REQUESTS",
            "message": f"Demo generation is limited to {GENERATE_LIMIT_PER_HOUR} per hour. "
                       "Already-built demos are still available.",
        }), 429

    product = _find_product(product_id)
    if not product:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": "Product not found."}), 404

    slug = DemoRepository.slug_for(product)
    if not slug:
        return jsonify({"success": False, "error": "NOT_FOUND", "message": "Product has no usable name."}), 404

    body = request.get_json(silent=True) or {}
    if body.get("refresh") is not True:
        existing = DemoRepository.get(slug)
        if existing:
            return jsonify({"success": True, "data": existing, "cached": True})

    result = demo_service.generate(product, slug)
    if not result.get("success"):
        code = result.get("error", "INVALID_SPEC")
        status_code = {"NOT_CONFIGURED": 503, "PROVIDER_UNAVAILABLE": 503}.get(code, 502)
        return jsonify({
            "success": False,
            "error": code,
            "message": {
                "NOT_CONFIGURED": "Demo generation is not connected yet. Pre-built demos still work.",
                "PROVIDER_UNAVAILABLE": "The generator is unavailable right now. Please try again.",
            }.get(code, "The generated demo did not pass validation. Please try again."),
            "detail": result.get("detail", ""),
        }), status_code

    DemoRepository.save(result["spec"])
    return jsonify({"success": True, "data": result["spec"], "cached": False})


@demos_bp.route("/live", methods=["POST"])
def live_query():
    ip = _client_ip()
    if not _allow(_live_tracker, ip, LIVE_LIMIT_PER_MINUTE, 60):
        return jsonify({"success": False, "error": "TOO_MANY_REQUESTS"}), 429
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"success": False, "error": "BAD_REQUEST"}), 400
    endpoint_id = body.get("endpoint_id")
    if not isinstance(endpoint_id, str) or not endpoint_id:
        return jsonify({"success": False, "error": "BAD_REQUEST"}), 400
    result = demo_service.run_live_query(endpoint_id, body.get("query", ""))
    return jsonify(result), 200 if result.get("success") else 502


# Registered last: a bare "/<product_id>" would otherwise shadow "/status".
@demos_bp.route("/<path:product_id>", methods=["GET"])
def get_demo(product_id):
    spec = DemoRepository.get(product_id)
    if not spec:
        product = _find_product(product_id)
        if product:
            spec = DemoRepository.get(DemoRepository.slug_for(product))
    if not spec:
        return jsonify({
            "success": False,
            "data": None,
            "error": "NOT_GENERATED",
            "generation_available": demo_service.is_configured(),
        }), 404
    return jsonify({"success": True, "data": spec})
