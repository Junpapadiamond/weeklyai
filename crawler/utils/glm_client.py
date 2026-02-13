#!/usr/bin/env python3
"""
GLM (智谱) API Client for WeeklyAI

用于中国区 AI 产品发现，使用智谱 GLM 联网搜索 API。

API 文档: https://open.bigmodel.cn/dev/api

支持功能：
1. Web Search API: 联网搜索（search_pro / search_pro_sogou）
2. Chat API: GLM-4 模型分析
3. 组合方法: 搜索 + 分析一体化

Usage:
    from utils.glm_client import GLMClient

    client = GLMClient(api_key="your-key")

    # 方式1: 纯搜索
    results = client.search("AI融资 2026")

    # 方式2: 搜索 + 分析
    products = client.search_and_extract(
        query="AI创业公司 融资 2026",
        analysis_prompt="Extract AI products...",
        region="cn"
    )
"""

import os
import json
import time
import re
import requests
from typing import Optional, Union
from dataclasses import dataclass, field

# ════════════════════════════════════════════════════════════════════════════════
# 全局配置
# ════════════════════════════════════════════════════════════════════════════════

ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
GLM_MODEL = os.environ.get('GLM_MODEL', 'glm-4.7')  # 最新: glm-4.7 (200K context, 128K output)
GLM_SEARCH_ENGINE = os.environ.get('GLM_SEARCH_ENGINE', 'search_pro')  # search_pro / search_pro_sogou / search_pro_quark
API_RATE_LIMIT_DELAY = float(os.environ.get('API_RATE_LIMIT_DELAY', '2'))
API_MAX_RETRIES = int(os.environ.get('API_MAX_RETRIES', '3'))
API_RETRY_BACKOFF = float(os.environ.get('API_RETRY_BACKOFF', '2'))
GLM_THINKING_TYPE = os.environ.get('GLM_THINKING_TYPE', 'disabled')  # enabled/disabled
GLM_CLEAR_THINKING = os.environ.get('GLM_CLEAR_THINKING', 'true').lower() == 'true'
USE_GLM_FOR_CN = os.environ.get('USE_GLM_FOR_CN', 'true').lower() == 'true'

# 独立 Web Search API 端点
GLM_WEB_SEARCH_URL = "https://open.bigmodel.cn/api/paas/v4/web_search"

# GLM-4.7 默认采样参数
GLM_DEFAULT_TEMPERATURE = 1.0  # GLM-4.7 默认值
GLM_DEFAULT_TOP_P = 0.95       # GLM-4.7 默认值

# 搜索引擎配置
SEARCH_ENGINES = {
    "search_pro": {
        "name": "智谱高阶搜索",
        "price": "¥0.03/次",
        "description": "智谱自研高阶版，适合通用搜索"
    },
    "search_pro_sogou": {
        "name": "搜狗高阶搜索",
        "price": "¥0.05/次",
        "description": "腾讯生态+知乎，适合中文内容深度搜索"
    },
    "search_pro_quark": {
        "name": "夸克高阶搜索",
        "price": "¥0.05/次",
        "description": "夸克搜索增强，适合中文站点召回"
    },
    "search_std": {
        "name": "标准搜索",
        "price": "¥0.01/次",
        "description": "基础搜索，适合简单查询"
    }
}

# 中国权威 AI 媒体域名（用于过滤优质结果）
CN_TRUSTED_DOMAINS = [
    "36kr.com",
    "jiqizhixin.com",
    "itjuzi.com",
    "tmtpost.com",
    "qbitai.com",
    "leiphone.com",
    "thepaper.cn",
    "geekpark.net",
]


# ════════════════════════════════════════════════════════════════════════════════
# 数据类（与 Perplexity 客户端保持一致）
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.snippet,
            "date": self.date,
            "source": self.source
        }

    def format_for_prompt(self) -> str:
        """格式化为 Prompt 文本"""
        lines = [f"### {self.title}"]
        lines.append(f"Source URL: {self.url}")
        if self.date:
            lines.append(f"Date: {self.date}")
        if self.source:
            lines.append(f"Source: {self.source}")
        lines.append(f"Content: {self.snippet}")
        return "\n".join(lines)


@dataclass
class ExtractionResult:
    """提取结果"""
    products: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    raw_response: str = ""
    search_count: int = 0
    extract_count: int = 0


# ════════════════════════════════════════════════════════════════════════════════
# GLM 客户端
# ════════════════════════════════════════════════════════════════════════════════

class GLMClient:
    """
    智谱 GLM API 客户端

    默认使用 GLM-4.7 模型，特性：
    - 最大上下文 200K，最大输出 128K
    - 支持深度思考 (thinking)
    - 支持流式工具调用

    支持：
    - Web Search Tool: 联网搜索
    - Chat Completions API: GLM 模型分析
    - 组合方法: 搜索 + 分析一体化
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ZHIPU_API_KEY
        self.model = GLM_MODEL
        self.search_engine = GLM_SEARCH_ENGINE
        self._client = None
        self._search_session = None

        if self.api_key:
            # Setup requests.Session for direct Web Search API
            self._search_session = requests.Session()
            self._search_session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            # Setup ZhipuAI SDK for analyze() (chat completions)
            try:
                from zhipuai import ZhipuAI
                self._client = ZhipuAI(api_key=self.api_key)
            except ImportError:
                print("⚠️ zhipuai SDK not installed. Run: pip install zhipuai")
        else:
            print("⚠️ ZHIPU_API_KEY not set")

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._search_session is not None or self._client is not None

    def _rate_limit(self):
        """API 限流"""
        time.sleep(API_RATE_LIMIT_DELAY)

    def _is_rate_limited(self, error: Exception) -> bool:
        """判断是否触发限流"""
        msg = str(error)
        return ("Error code: 429" in msg) or ("1302" in msg) or ("并发数过高" in msg)

    # ════════════════════════════════════════════════════════════════════════════
    # Web Search (独立 Web Search API)
    # ════════════════════════════════════════════════════════════════════════════

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_engine: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        使用智谱独立 Web Search API 搜索

        直接调用 POST /paas/v4/web_search，返回结构化搜索结果（真实 URL）。
        不经过 GLM 模型，避免幻觉 URL。

        Args:
            query: 搜索查询
            max_results: 期望结果数量 (最大 50)
            search_engine: 搜索引擎 (search_pro/search_pro_sogou/search_pro_quark/search_std)

        Returns:
            SearchResult 列表
        """
        if not self._search_session:
            return []

        engine = search_engine or self.search_engine
        print(f"  🔍 GLM Web Search API ({engine}): {query[:50]}...")

        payload = {
            "search_query": query,
            "search_engine": engine,
            "search_intent": False,
            "count": min(max_results, 50),
            "content_size": "medium",
            "search_recency_filter": "oneWeek",
        }

        last_error: Optional[Exception] = None
        for attempt in range(1, API_MAX_RETRIES + 1):
            try:
                resp = self._search_session.post(
                    GLM_WEB_SEARCH_URL, json=payload, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("search_result", []):
                    url = (item.get("link") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not url or not title:
                        continue
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=(item.get("content") or "").strip(),
                        date=item.get("publish_date"),
                        source=item.get("media"),
                    ))

                print(f"  ✅ Found {len(results)} results")
                return results[:max_results]

            except requests.exceptions.HTTPError as e:
                last_error = e
                status = e.response.status_code if e.response is not None else 0
                if status == 429 and attempt < API_MAX_RETRIES:
                    wait = API_RATE_LIMIT_DELAY * (API_RETRY_BACKOFF ** (attempt - 1))
                    print(f"  ⏳ GLM rate limited, retrying in {wait:.1f}s "
                          f"(attempt {attempt}/{API_MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                print(f"  ❌ GLM Web Search HTTP Error ({status}): {e}")
                break
            except Exception as e:
                last_error = e
                if self._is_rate_limited(e) and attempt < API_MAX_RETRIES:
                    wait = API_RATE_LIMIT_DELAY * (API_RETRY_BACKOFF ** (attempt - 1))
                    print(f"  ⏳ GLM rate limited, retrying in {wait:.1f}s "
                          f"(attempt {attempt}/{API_MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                print(f"  ❌ GLM Web Search Error: {e}")
                break
            finally:
                self._rate_limit()

        if last_error and (
            self._is_rate_limited(last_error)
            or (isinstance(last_error, requests.exceptions.HTTPError)
                and last_error.response is not None
                and last_error.response.status_code == 429)
        ):
            print("  ⚠️ GLM search failed due to rate limit; consider reducing traffic or "
                  "raising API concurrency limits.")
        return []

    def search_by_region(
        self,
        query: str,
        region: str = "cn",
        max_results: int = 10,
        **kwargs
    ) -> list[SearchResult]:
        """
        按地区搜索（GLM 主要服务中国区）

        Args:
            query: 搜索查询
            region: 地区代码 (cn)
            max_results: 结果数量
        """
        # GLM 主要用于中国区搜索，其他地区应使用 Perplexity
        if region != "cn":
            print(f"  ⚠️ GLM is optimized for CN region, got: {region}")

        return self.search(query, max_results=max_results, **kwargs)

    # ════════════════════════════════════════════════════════════════════════════
    # Chat Completions API (分析内容)
    # ════════════════════════════════════════════════════════════════════════════

    def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        top_p: Optional[float] = None
    ) -> Union[dict, list, str]:
        """
        使用 GLM 模型分析内容

        GLM-4.7 采样参数说明：
        - temperature: 默认 1.0，控制随机性（更高更发散，更低更稳定）
        - top_p: 默认 0.95，控制核采样（更高扩大候选集，更低收敛候选集）
        - 建议只调整其中一个参数，不要同时调整

        Args:
            prompt: 完整 prompt (包含搜索结果和指令)
            model: 模型 (glm-4.7/glm-4-flash)
            temperature: 温度 (0-2，推荐 0.3 以获得稳定输出用于提取任务)
            max_tokens: 最大 token (GLM-4.7 支持最大 128K)
            top_p: 核采样参数 (可选，与 temperature 二选一)

        Returns:
            解析后的 JSON 或原始文本
        """
        if not self._client:
            return {}

        model = model or self.model

        # 构建请求参数
        request_params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "thinking": {
                "type": GLM_THINKING_TYPE,
                "clear_thinking": GLM_CLEAR_THINKING
            }
        }

        # 使用 temperature 或 top_p（建议只用一个）
        if top_p is not None:
            request_params["top_p"] = top_p
        else:
            request_params["temperature"] = temperature

        last_error: Optional[Exception] = None
        for attempt in range(1, API_MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(**request_params)

                result_text = response.choices[0].message.content or ""
                return self._extract_json(result_text)

            except Exception as e:
                last_error = e
                if self._is_rate_limited(e) and attempt < API_MAX_RETRIES:
                    wait = API_RATE_LIMIT_DELAY * (API_RETRY_BACKOFF ** (attempt - 1))
                    print(f"  ⏳ GLM rate limited, retrying in {wait:.1f}s "
                          f"(attempt {attempt}/{API_MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                print(f"  ❌ GLM Analyze Error: {e}")
                break
            finally:
                self._rate_limit()

        if last_error and self._is_rate_limited(last_error):
            print("  ⚠️ GLM analysis failed due to rate limit; consider reducing traffic or "
                  "raising API concurrency limits.")
        return {}

    def _extract_json(self, text: str) -> Union[dict, list, str]:
        """从文本中提取 JSON.

        Returns parsed JSON (list or dict) on success.
        Returns [] on parse failure so callers never receive raw text
        that masquerades as valid data.
        """
        if not text:
            return []

        # 尝试 ```json ... ``` 块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试找到 JSON 数组
        array_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', text)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        # 尝试找到 JSON 对象
        object_match = re.search(r'\{\s*"[\s\S]*\}', text)
        if object_match:
            try:
                return json.loads(object_match.group())
            except json.JSONDecodeError:
                pass

        # All parsing attempts failed — log and return empty list
        snippet = text[:200].replace('\n', ' ')
        print(f"  ⚠ _extract_json: could not parse response (first 200 chars): {snippet}")
        return []

    # ════════════════════════════════════════════════════════════════════════════
    # 组合方法：搜索 + 分析
    # ════════════════════════════════════════════════════════════════════════════

    def search_and_extract(
        self,
        query: str,
        analysis_prompt: str,
        region: str = "cn",
        max_results: int = 10,
        **search_kwargs
    ) -> ExtractionResult:
        """
        搜索并提取产品信息（推荐方法）

        工作流程:
        1. Web Search 获取搜索结果
        2. 格式化搜索结果
        3. GLM 分析并提取产品

        Args:
            query: 搜索查询
            analysis_prompt: 分析 Prompt，需包含 {search_results} 占位符
            region: 地区代码 (cn)
            max_results: 搜索结果数量

        Returns:
            ExtractionResult 包含产品列表和来源
        """
        result = ExtractionResult()

        # Step 1: 搜索
        search_results = self.search_by_region(query, region, max_results, **search_kwargs)
        result.search_count = len(search_results)
        result.sources = [r.url for r in search_results]

        if not search_results:
            return result

        # Step 2: 格式化搜索结果
        formatted_results = "\n\n".join([r.format_for_prompt() for r in search_results])

        # Step 3: 构建 prompt 并分析
        full_prompt = analysis_prompt.replace("{search_results}", formatted_results)

        print(f"    📊 Analyzing with GLM ({self.model})...")
        analysis = self.analyze(full_prompt)

        if isinstance(analysis, list):
            result.products = analysis
            result.extract_count = len(analysis)
        elif isinstance(analysis, dict):
            result.products = analysis.get("products", [analysis])
            result.extract_count = len(result.products)
        else:
            result.raw_response = str(analysis)

        print(f"    ✅ Extracted {result.extract_count} products")
        return result

    def format_results_for_prompt(self, results: list[SearchResult]) -> str:
        """格式化搜索结果为 Prompt 文本"""
        return "\n\n".join([r.format_for_prompt() for r in results])

    # ════════════════════════════════════════════════════════════════════════════
    # 便捷方法
    # ════════════════════════════════════════════════════════════════════════════

    def get_status(self) -> dict:
        """获取客户端状态"""
        return {
            "available": self.is_available(),
            "api_key_set": bool(self.api_key),
            "model": self.model,
            "search_engine": self.search_engine,
            "search_mode": "direct_api",
            "search_engine_info": SEARCH_ENGINES.get(self.search_engine, {}),
            "thinking": {
                "type": GLM_THINKING_TYPE,
                "clear_thinking": GLM_CLEAR_THINKING
            }
        }


# ════════════════════════════════════════════════════════════════════════════════
# 便捷函数（与 Perplexity 客户端接口一致）
# ════════════════════════════════════════════════════════════════════════════════

_default_client: Optional[GLMClient] = None


def get_client() -> GLMClient:
    """获取默认客户端（单例）"""
    global _default_client
    if _default_client is None:
        _default_client = GLMClient()
    return _default_client


def glm_search(query: str, max_results: int = 10, region: str = "cn", **kwargs) -> list[dict]:
    """
    快速搜索

    Returns:
        [{"title": "", "url": "", "content": ""}, ...]
    """
    client = get_client()
    results = client.search_by_region(query, region, max_results, **kwargs)
    return [r.to_dict() for r in results]


def glm_analyze(prompt: str, **kwargs) -> Union[dict, list]:
    """快速分析"""
    client = get_client()
    return client.analyze(prompt, **kwargs)


def is_glm_available() -> bool:
    """检查 GLM 是否可用"""
    return bool(ZHIPU_API_KEY) and USE_GLM_FOR_CN


# ════════════════════════════════════════════════════════════════════════════════
# 测试
# ════════════════════════════════════════════════════════════════════════════════

def test_client():
    """测试客户端"""
    print("\n" + "="*60)
    print("  🧪 Testing GLM Client (智谱)")
    print("="*60)

    client = GLMClient()
    print(f"\n  Status: {client.get_status()}")

    if not client.is_available():
        print("\n  ❌ API key not set or SDK not installed.")
        print("  Set ZHIPU_API_KEY env var and run: pip install zhipuai")
        return False

    # Test 1: 基础搜索
    print("\n  📍 Test 1: Basic Search (中国 AI 融资)")
    results = client.search("AI创业公司 融资 2026", max_results=3)
    if results:
        for i, r in enumerate(results, 1):
            print(f"    {i}. {r.title[:50]}...")
            print(f"       URL: {r.url}")
            print(f"       Date: {r.date}")
    else:
        print("    ⚠️ No results (may need to check API)")

    # Test 2: 分析
    print("\n  📍 Test 2: GLM Analysis")
    test_prompt = """基于以下信息，提取公司名称和网站：

### 示例新闻
某AI创业公司完成A轮融资，金额5000万美元，官网 https://example.com

返回 JSON 格式: {"name": "...", "website": "..."}"""

    analysis = client.analyze(test_prompt, temperature=0.1)
    print(f"    Result: {analysis}")

    print("\n  ✅ GLM test completed!")
    return True


if __name__ == "__main__":
    test_client()
