"""
Chat API blueprint for WeeklyAI.

Routes:
- GET /api/v1/chat/status
- POST /api/v1/chat (JSON or SSE)
"""

from __future__ import annotations

from collections import defaultdict
import os
import time

from flask import Blueprint, Response, jsonify, request

from app.services.env_utils import sanitize_env_value

chat_bp = Blueprint("chat", __name__)

_chat_rate_tracker: dict[str, list[float]] = defaultdict(list)
CHAT_RATE_LIMIT = 10
MAX_MESSAGE_LENGTH = 2000


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    return forwarded.split(",")[0].strip()


def _is_chat_allowed(ip: str) -> bool:
    now = time.time()
    minute_ago = now - 60
    _chat_rate_tracker[ip] = [t for t in _chat_rate_tracker[ip] if t > minute_ago]
    if len(_chat_rate_tracker[ip]) >= CHAT_RATE_LIMIT:
        return False
    _chat_rate_tracker[ip].append(now)
    return True


def _wants_sse(body: dict) -> bool:
    query_stream = str(request.args.get("stream", "")).strip().lower() in {"1", "true", "yes"}
    body_stream = str(body.get("stream", "")).strip().lower() in {"1", "true", "yes"}
    accept_header = (request.headers.get("Accept", "") or "").lower()
    header_stream = "text/event-stream" in accept_header
    return query_stream or body_stream or header_stream


@chat_bp.route("/status", methods=["GET"])
def chat_status():
    key = sanitize_env_value(os.environ.get("PERPLEXITY_API_KEY", ""))
    model = sanitize_env_value(os.environ.get("PERPLEXITY_CHAT_MODEL", "sonar"), "sonar") or "sonar"
    return jsonify(
        {
            "success": True,
            "has_api_key": bool(key and len(key) > 5),
            "provider": "perplexity",
            "model": model,
            "rate_limit_per_minute": CHAT_RATE_LIMIT,
        }
    )


@chat_bp.route("", methods=["POST"])
def chat():
    client_ip = _client_ip()
    if not _is_chat_allowed(client_ip):
        return (
            jsonify(
                {
                    "success": False,
                    "content": "Chat rate limit exceeded. Please wait a moment.",
                    "error": "TOO_MANY_REQUESTS",
                }
            ),
            429,
        )

    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    locale = str(body.get("locale", "zh")).strip()

    if not message:
        return (
            jsonify(
                {
                    "success": False,
                    "content": "Message is required.",
                    "error": "BAD_REQUEST",
                }
            ),
            400,
        )

    if len(message) > MAX_MESSAGE_LENGTH:
        return (
            jsonify(
                {
                    "success": False,
                    "content": f"Message too long (max {MAX_MESSAGE_LENGTH} chars).",
                    "error": "BAD_REQUEST",
                }
            ),
            400,
        )

    wants_sse = _wants_sse(body)

    if wants_sse:
        from app.services.chat_service import stream_chat_response

        return Response(
            stream_chat_response(message=message, locale=locale),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    from app.services.chat_service import get_chat_response

    return jsonify(get_chat_response(message=message, locale=locale))
