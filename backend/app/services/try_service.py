"""
Try-it-now service — streams a lightweight LLM simulation of a product's
core feature based on the product's pre-generated experience config.
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


def _sse_event(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _clean(text: str) -> str:
    value = re.sub(r"\[(?:\d+(?:\s*[-,，]\s*\d+)*)\]", "", text or "")
    return re.sub(r"[ \t]{2,}", " ", value).strip()


def _build_system_prompt(product: dict[str, Any], locale: str) -> str:
    name = product.get("name", "")
    description = product.get("description") or product.get("description_en") or ""
    why_matters = product.get("why_matters") or product.get("why_matters_en") or ""
    extra = product.get("extra") or {}
    experience = extra.get("experience") or {}
    template = experience.get("demo_prompt_template", "")

    if locale == "en":
        base = (
            f"You are a concise, helpful simulator of {name}.\n"
            f"Product description: {description}\n"
            f"Key value: {why_matters}\n"
        )
    else:
        base = (
            f"你是 {name} 的精简功能模拟器，只展示该产品的核心价值。\n"
            f"产品描述：{description}\n"
            f"核心价值：{why_matters}\n"
        )

    if template:
        base += f"\n{template}"

    if locale == "en":
        base += "\n\nRespond concisely (≤200 words). Be specific and directly useful."
    else:
        base += "\n\n请简洁回答（不超过200字），直接给出有用的产出，体现该产品的核心功能。"

    return base


def stream_try_response(
    product: dict[str, Any],
    user_input: str,
    locale: str = "zh",
) -> Generator[str, None, None]:
    """Yield SSE events simulating the product's core feature."""
    normalized_locale = "en" if locale.strip().lower() in ("en", "en-us") else "zh"

    # Check demo_type — static/iframe types shouldn't reach here, but guard anyway
    extra = product.get("extra") or {}
    experience = extra.get("experience") or {}
    demo_type = experience.get("demo_type", "text_generation")
    fallback_url = experience.get("fallback_url", "")

    if demo_type in ("iframe", "static"):
        yield _sse_event({"type": "redirect", "url": fallback_url})
        yield _sse_event({"type": "done"})
        return

    api_key = _get_api_key()
    if not api_key:
        msg = "AI assistant is not configured." if normalized_locale == "en" else "AI 助手暂不可用（API 未配置）。"
        yield _sse_event({"type": "error", "message": msg})
        yield _sse_event({"type": "done"})
        return

    payload = {
        "model": _get_model(),
        "messages": [
            {"role": "system", "content": _build_system_prompt(product, normalized_locale)},
            {"role": "user", "content": user_input},
        ],
        "max_tokens": 400,
        "temperature": 0.5,
        "stream": True,
    }

    try:
        response = requests.post(
            PERPLEXITY_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            stream=True,
            timeout=20,
        )
    except requests.exceptions.Timeout:
        msg = "Request timed out." if normalized_locale == "en" else "请求超时，请重试。"
        yield _sse_event({"type": "error", "message": msg})
        yield _sse_event({"type": "done"})
        return
    except Exception:
        msg = "Unexpected error." if normalized_locale == "en" else "发生未知错误，请稍后重试。"
        yield _sse_event({"type": "error", "message": msg})
        yield _sse_event({"type": "done"})
        return

    if response.status_code != 200:
        yield _sse_event({"type": "error", "message": f"API error ({response.status_code})"})
        yield _sse_event({"type": "done"})
        return

    try:
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            chunk_raw = line[5:].strip()
            if chunk_raw == "[DONE]":
                break
            try:
                chunk = json.loads(chunk_raw)
            except Exception:
                continue
            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = (choices[0] if isinstance(choices[0], dict) else {}).get("delta", {})
            content = str(delta.get("content", "")) if isinstance(delta, dict) else ""
            if content:
                yield _sse_event({"type": "text", "content": content})
        yield _sse_event({"type": "done"})
    except Exception:
        msg = "Stream error." if normalized_locale == "en" else "流式输出中断，请重试。"
        yield _sse_event({"type": "error", "message": msg})
        yield _sse_event({"type": "done"})
