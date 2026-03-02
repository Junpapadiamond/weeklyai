"""
爬虫基类
"""

from __future__ import annotations

import os
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from requests import Response
from requests.exceptions import RequestException


def _env_int(name: str, default: int, min_value: int, max_value: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except Exception:
        return default
    return max(min_value, min(max_value, value))


def _env_float(name: str, default: float, min_value: float, max_value: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except Exception:
        return default
    return max(min_value, min(max_value, value))


class BaseSpider(ABC):
    """爬虫基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.products = []
        self.retry_status_codes: Set[int] = {429, 500, 502, 503, 504}
        self.max_retries = _env_int("SOCIAL_HTTP_MAX_RETRIES", default=3, min_value=1, max_value=8)
        self.backoff_seconds = _env_float("SOCIAL_HTTP_BACKOFF_SECONDS", default=1.5, min_value=0.1, max_value=30.0)
        self.jitter_seconds = _env_float("SOCIAL_HTTP_JITTER_SECONDS", default=0.4, min_value=0.0, max_value=5.0)
        self.connect_timeout = _env_float("SOCIAL_CONNECT_TIMEOUT", default=10.0, min_value=1.0, max_value=60.0)
        self.read_timeout = _env_float("SOCIAL_READ_TIMEOUT", default=20.0, min_value=1.0, max_value=180.0)
    
    @abstractmethod
    def crawl(self) -> List[Dict[str, Any]]:
        """
        执行爬取操作
        返回产品列表
        """
        pass
    
    def _resolve_timeout(self, timeout: Optional[Any] = None) -> Any:
        if timeout is not None:
            return timeout
        return (self.connect_timeout, self.read_timeout)

    def _retry_sleep(self, attempt: int) -> None:
        # Exponential backoff with bounded random jitter.
        delay = self.backoff_seconds * (2 ** max(0, attempt - 1))
        if self.jitter_seconds > 0:
            delay += random.uniform(0.0, self.jitter_seconds)
        time.sleep(delay)

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: Optional[Any] = None,
        max_retries: Optional[int] = None,
        retry_status_codes: Optional[Set[int]] = None,
        **kwargs,
    ) -> Response:
        retries = max(1, int(max_retries or self.max_retries))
        retry_status = retry_status_codes or self.retry_status_codes
        timeout_value = self._resolve_timeout(timeout)

        last_error: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                response = self.session.request(method, url, timeout=timeout_value, **kwargs)
            except RequestException as exc:
                last_error = exc
                if attempt >= retries:
                    raise
                self._retry_sleep(attempt)
                continue

            if response.status_code in retry_status and attempt < retries:
                self._retry_sleep(attempt)
                continue

            response.raise_for_status()
            return response

        if last_error:
            raise last_error
        raise RuntimeError(f"request failed without response: {method} {url}")

    def fetch(self, url: str, **kwargs) -> Response:
        """
        发送HTTP请求（默认 GET + 统一重试策略）
        """
        try:
            return self.request("GET", url, **kwargs)
        except Exception as e:
            print(f"请求失败 {url}: {e}")
            raise
    
    def create_product(self, name: str, description: str, logo_url: str,
                       website: str, categories: List[str], **kwargs) -> Dict[str, Any]:
        """
        创建标准化的产品数据
        """
        product = {
            'name': name,
            'description': description,
            'logo_url': logo_url,
            'website': website,
            'categories': categories,
            'rating': kwargs.get('rating', 0),
            'weekly_users': kwargs.get('weekly_users', 0),
            'trending_score': kwargs.get('trending_score', 0),
            'is_hardware': kwargs.get('is_hardware', False),
            'source': kwargs.get('source', 'unknown'),
        }

        extra = kwargs.get('extra', {}) or {}
        if 'published_at' in kwargs and 'published_at' not in extra:
            extra['published_at'] = kwargs.get('published_at')
        if 'release_year' in kwargs and 'release_year' not in extra:
            extra['release_year'] = kwargs.get('release_year')
        if 'price' in kwargs and 'price' not in extra:
            extra['price'] = kwargs.get('price')
        if extra:
            product['extra'] = extra
            if 'published_at' in extra:
                product['published_at'] = extra['published_at']
            if 'release_year' in extra:
                product['release_year'] = extra['release_year']
            if 'price' in extra:
                product['price'] = extra['price']

        return product


