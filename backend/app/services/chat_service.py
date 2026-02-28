"""
Chat service for WeeklyAI.

Supports both:
- JSON (non-stream, Vercel-stable)
- SSE stream (real-time UX)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Generator

import requests

from app.services.env_utils import sanitize_env_value

PERPLEXITY_CHAT_URL = "https://api.perplexity.ai/chat/completions"


def _get_api_key() -> str:
    return sanitize_env_value(os.environ.get("PERPLEXITY_API_KEY", ""))


def _get_model() -> str:
    return sanitize_env_value(os.environ.get("PERPLEXITY_CHAT_MODEL", "sonar"), "sonar") or "sonar"


def _normalize_locale(locale: str | None) -> str:
    value = (locale or "zh").strip().lower()
    if value in ("en", "en-us"):
        return "en"
    return "zh"


def _clean_output(text: str) -> str:
    # Remove common citation markers like [1][2].
    return re.sub(r"\[\d+\]", "", text or "").strip()


def _shorten(text: str, max_len: int = 220) -> str:
    trimmed = (text or "").strip()
    if len(trimmed) <= max_len:
        return trimmed
    return f"{trimmed[: max_len - 1]}…"


def _extract_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message", {})
    if not isinstance(message, dict):
        return ""
    return str(message.get("content", "")).strip()


def _build_product_context() -> str:
    try:
        from app.services.product_service import ProductService

        dark_horses = ProductService.get_dark_horse_products(limit=6, min_index=4)
        rising = ProductService.get_rising_star_products(limit=4)
    except Exception:
        dark_horses = []
        rising = []

    lines: list[str] = []
    if dark_horses:
        lines.append("=== Dark Horses (4-5) ===")
        for item in dark_horses[:6]:
            name = str(item.get("name", "")).strip() or "Unknown"
            score = item.get("dark_horse_index", "")
            funding = str(item.get("funding_total", "")).strip() or "n/a"
            reason = _shorten(
                str(item.get("why_matters", "")).strip() or str(item.get("description", "")).strip()
            )
            lines.append(f"- {name} ({score}): {reason} | Funding: {funding}")

    if rising:
        lines.append("=== Rising Stars (2-3) ===")
        for item in rising[:4]:
            name = str(item.get("name", "")).strip() or "Unknown"
            score = item.get("dark_horse_index", "")
            reason = _shorten(
                str(item.get("why_matters", "")).strip() or str(item.get("description", "")).strip()
            )
            lines.append(f"- {name} ({score}): {reason}")

    return "\n".join(lines) if lines else "No product data available."


def _build_system_prompt(locale: str) -> str:
    product_context = _build_product_context()
    if locale == "en":
        return (
            "You are the WeeklyAI assistant.\n"
            "Answer only AI product questions based on the data below.\n"
            "Keep it concise, practical, and specific.\n"
            "Mention name, score, and key differentiator when recommending.\n\n"
            f"{product_context}"
        )

    return (
        "你是 WeeklyAI 助手。\n"
        "请基于下方产品数据回答 AI 产品相关问题。\n"
        "回答要简洁、具体、可执行。\n"
        "做推荐时请提到产品名、评分和关键差异点。\n\n"
        f"{product_context}"
    )


def _request_payload(message: str, locale: str, stream: bool) -> dict[str, Any]:
    return {
        "model": _get_model(),
        "messages": [
            {"role": "system", "content": _build_system_prompt(locale)},
            {"role": "user", "content": message},
        ],
        "max_tokens": 512,
        "temperature": 0.3,
        "stream": stream,
    }


def _request_error_message(normalized_locale: str) -> str:
    return "An unexpected error occurred." if normalized_locale == "en" else "发生了未知错误，请稍后重试。"


def get_chat_response(message: str, locale: str | None = "zh") -> dict[str, Any]:
    normalized_locale = _normalize_locale(locale)
    api_key = _get_api_key()
    if not api_key:
        return {
            "success": False,
            "content": "AI assistant is not configured." if normalized_locale == "en" else "AI 助手暂不可用（API 未配置）。",
        }

    try:
        response = requests.post(
            PERPLEXITY_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=_request_payload(message=message, locale=normalized_locale, stream=False),
            timeout=9,
        )
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "content": "Request timed out. Please try again." if normalized_locale == "en" else "请求超时，请重试。",
        }
    except Exception:
        return {
            "success": False,
            "content": _request_error_message(normalized_locale),
        }

    if response.status_code != 200:
        error_text = response.text[:200]
        try:
            parsed = response.json()
            error_message = parsed.get("error", {}).get("message", "")
            if error_message:
                error_text = str(error_message)[:200]
        except Exception:
            pass
        return {
            "success": False,
            "content": f"Upstream API error ({response.status_code}): {error_text}",
        }

    try:
        payload = response.json()
    except Exception:
        return {
            "success": False,
            "content": "Failed to decode model response." if normalized_locale == "en" else "模型返回解析失败。",
        }

    content = _clean_output(_extract_content(payload))
    if not content:
        return {
            "success": False,
            "content": "No response generated." if normalized_locale == "en" else "未生成有效回答，请重试。",
        }

    return {"success": True, "content": content}


def _sse_event(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_chat_response(message: str, locale: str | None = "zh") -> Generator[str, None, None]:
    normalized_locale = _normalize_locale(locale)
    api_key = _get_api_key()
    if not api_key:
        yield _sse_event(
            {
                "type": "error",
                "message": "AI assistant is not configured." if normalized_locale == "en" else "AI 助手暂不可用（API 未配置）。",
            }
        )
        yield _sse_event({"type": "done"})
        return

    try:
        response = requests.post(
            PERPLEXITY_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=_request_payload(message=message, locale=normalized_locale, stream=True),
            stream=True,
            timeout=20,
        )
    except requests.exceptions.Timeout:
        yield _sse_event(
            {
                "type": "error",
                "message": "Request timed out. Please try again." if normalized_locale == "en" else "请求超时，请重试。",
            }
        )
        yield _sse_event({"type": "done"})
        return
    except Exception:
        yield _sse_event({"type": "error", "message": _request_error_message(normalized_locale)})
        yield _sse_event({"type": "done"})
        return

    if response.status_code != 200:
        error_text = response.text[:200]
        try:
            parsed = response.json()
            error_message = parsed.get("error", {}).get("message", "")
            if error_message:
                error_text = str(error_message)[:200]
        except Exception:
            pass
        yield _sse_event({"type": "error", "message": f"Upstream API error ({response.status_code}): {error_text}"})
        yield _sse_event({"type": "done"})
        return

    try:
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if not line.startswith("data:"):
                continue

            payload = line[5:].strip()
            if payload == "[DONE]":
                break

            try:
                chunk = json.loads(payload)
            except Exception:
                continue

            choices = chunk.get("choices", [])
            if not choices:
                continue
            choice = choices[0] if isinstance(choices[0], dict) else {}
            delta = choice.get("delta", {}) if isinstance(choice, dict) else {}
            if not isinstance(delta, dict):
                continue
            content = str(delta.get("content", ""))
            if content:
                yield _sse_event({"type": "text", "content": content})

        yield _sse_event({"type": "done"})
    except Exception:
        yield _sse_event({"type": "error", "message": _request_error_message(normalized_locale)})
        yield _sse_event({"type": "done"})
