"""No-account product experiences with persistent daily budgets."""
import hashlib
import os
import uuid
from flask import Blueprint, jsonify, request
from itsdangerous import URLSafeTimedSerializer, BadSignature
from app.services.demo_contract import cache_key
from app.services.demo_experiences import published, ready_experience, prepare_experience, provider_available
from app.services.demo_store import DemoStore, production
from app.services.product_service import ProductService

demos_bp = Blueprint("demos", __name__)
COOKIE = "weeklyai_demo_visitor"


def _context():
    secret = os.getenv("DEMO_COOKIE_SECRET", "")
    identity_ready = len(secret) >= 32 or not production()
    serializer = URLSafeTimedSerializer(secret if len(secret) >= 32 else "weeklyai-local-development-only", salt="demo-visitor-v1")
    cookie = request.cookies.get(COOKIE, "")
    try:
        identity = serializer.loads(cookie, max_age=30 * 86400)
        if not isinstance(identity, str) or len(identity) != 32:
            raise BadSignature("invalid identity")
    except BadSignature:
        identity = uuid.uuid4().hex
        cookie = serializer.dumps(identity)
    actor = hashlib.sha256(identity.encode()).hexdigest()[:32]
    try:
        store = DemoStore()
        quota = store.quota(actor)
    except Exception:
        store, quota = None, None
    return actor, cookie, identity_ready, store, quota


def _response(body, status, context):
    _, cookie, identity_ready, store, quota = context
    body.update(quota=quota, ai_available=provider_available(), generation_available=bool(identity_ready and store and provider_available()))
    response = jsonify(body)
    response.status_code = status
    response.headers["Cache-Control"] = "private, no-store"
    response.set_cookie(COOKIE, cookie, max_age=30 * 86400, httponly=True, secure=production(), samesite="Lax", path="/api/v1/demos")
    if status == 202:
        response.headers["Retry-After"] = "3"
    return response


@demos_bp.get("/status")
def demo_status():
    return _response({"success": True}, 200, _context())


@demos_bp.get("/catalog")
def demo_catalog():
    context = _context()
    keys = set(published())
    if context[3]:
        try:
            keys.update(context[3].keys())
        except Exception:
            context = (*context[:3], None, None)
    products = ProductService.get_discovery_products()
    ready = sum(cache_key(p) in keys for p in products)
    dark = sum(float(p.get("dark_horse_index") or 0) >= 4 for p in products)
    query, category = request.args.get("q", "").strip().lower()[:160], request.args.get("filter", "all")
    filtered = []
    for p in products:
        is_ready = cache_key(p) in keys
        if category == "ready" and not is_ready or category == "dark" and float(p.get("dark_horse_index") or 0) < 4:
            continue
        if query and query not in " ".join(str(p.get(k, "")) for k in ("name", "description", "description_en", "categories", "country_name")).lower():
            continue
        filtered.append(p)
    filtered.sort(key=lambda p: (cache_key(p) not in keys, -float(p.get("dark_horse_index") or 0), p["name"].lower()))
    try:
        page, limit = max(1, int(request.args.get("page", 1))), min(60, max(1, int(request.args.get("limit", 24))))
    except ValueError:
        return _response({"success": False, "error": "BAD_REQUEST"}, 400, context)
    fields = ("_id", "name", "website", "logo_url", "logo", "source_url", "description", "description_en", "categories", "country_name", "dark_horse_index", "is_hardware")
    items = [{**{k: p.get(k) for k in fields}, "_id": str(p.get("_id") or p["name"]), "demo_ready": cache_key(p) in keys}
             for p in filtered[(page - 1) * limit:page * limit]]
    return _response({"success": True, "products": items, "total": len(filtered), "catalog_total": len(products),
                      "ready_count": ready, "dark_count": dark, "page": page, "limit": limit}, 200, context)


@demos_bp.get("/product/<product_id>")
def demo_product(product_id):
    context = _context()
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return _response({"success": False, "error": "NOT_FOUND"}, 404, context)
    entry = ready_experience(product, context[3])
    return _response({"success": True, "state": "ready" if entry else "not_generated", "experience": entry}, 200, context)


@demos_bp.post("/generate")
def demo_generate():
    context = _context()
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("product_id"), str) or not 1 <= len(body["product_id"].strip()) <= 160:
        return _response({"success": False, "error": "BAD_REQUEST"}, 400, context)
    product = ProductService.get_product_by_id(body["product_id"].strip())
    if not product:
        return _response({"success": False, "error": "NOT_FOUND"}, 404, context)
    actor, _, identity_ready, store, _ = context
    entry = ready_experience(product, store)
    if entry:
        return _response({"success": True, "state": "ready", "cached": True, "experience": entry}, 200, context)
    if not identity_ready:
        return _response({"success": False, "error": "IDENTITY_NOT_CONFIGURED"}, 503, context)
    try:
        result, status = prepare_experience(product, actor, store)
        context = (*context[:4], store.quota(actor) if store else None)
    except Exception:
        result, status = {"success": False, "error": "STORAGE_UNAVAILABLE"}, 503
    return _response(result, status, context)
