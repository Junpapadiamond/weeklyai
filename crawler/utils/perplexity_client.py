#!/usr/bin/env python3
"""
Perplexity API Client v2.0

采用 Search API + Sonar 两步走方案：
1. Search API: 获取结构化搜索结果 (title, url, snippet, date)
2. Sonar Model: 分析搜索结果，提取产品信息

优点：
- 搜索结果可控，可以过滤低质量来源
- 官网提取更准确
- 成本可控（Search API 比 Sonar 便宜）

Usage:
    from utils.perplexity_client import PerplexityClient
    
    client = PerplexityClient(api_key="your-key")
    
    # 方式1: 纯搜索
    results = client.search("AI startup funding 2026")
    
    # 方式2: 搜索 + 分析
    products = client.search_and_extract(
        query="AI startup funding 2026",
        analysis_prompt="Extract AI products...",
        region="us"
    )
"""

import os
import json
import time
import re
from typing import Optional, Union
from dataclasses import dataclass, field
import requests

# ════════════════════════════════════════════════════════════════════════════════
# 全局配置
# ════════════════════════════════════════════════════════════════════════════════

PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')
PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar')  # sonar / sonar-pro
API_RATE_LIMIT_DELAY = float(os.environ.get('API_RATE_LIMIT_DELAY', '2'))

# API 端点
SEARCH_API_URL = "https://api.perplexity.ai/search"
CHAT_API_URL = "https://api.perplexity.ai/chat/completions"

# 地区配置
REGION_CONFIG = {
    "us": {"country": "US", "languages": ["en"], "recency": "week"},
    "cn": {"country": "CN", "languages": ["zh"], "recency": "week"},
    "eu": {"country": "GB", "languages": ["en", "de", "fr"], "recency": "week"},
    "jp": {"country": "JP", "languages": ["ja", "en"], "recency": "week"},
    "kr": {"country": "KR", "languages": ["ko", "en"], "recency": "week"},
    "sea": {"country": "SG", "languages": ["en"], "recency": "week"},
}


# ════════════════════════════════════════════════════════════════════════════════
# 数据类
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    last_updated: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.snippet,
            "date": self.date,
            "last_updated": self.last_updated
        }
    
    def format_for_prompt(self) -> str:
        """格式化为 Prompt 文本"""
        lines = [f"### {self.title}"]
        lines.append(f"Source URL: {self.url}")
        if self.date:
            lines.append(f"Date: {self.date}")
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
# Perplexity 客户端
# ════════════════════════════════════════════════════════════════════════════════

class PerplexityClient:
    """
    Perplexity API 客户端
    
    支持：
    - Search API: 实时 Web 搜索
    - Chat Completions API: Sonar 模型分析
    - 组合方法: 搜索 + 分析一体化
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PERPLEXITY_API_KEY
        self.model = PERPLEXITY_MODEL
        self._session = requests.Session()
        
        if self.api_key:
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        else:
            print("⚠️ PERPLEXITY_API_KEY not set")
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key)
    
    def _rate_limit(self):
        """API 限流"""
        time.sleep(API_RATE_LIMIT_DELAY)
    
    # ════════════════════════════════════════════════════════════════════════════
    # Search API (第一步：获取搜索结果)
    # ════════════════════════════════════════════════════════════════════════════
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        country: Optional[str] = None,
        language_filter: Optional[list] = None,
        domain_filter: Optional[list] = None,
        recency_filter: Optional[str] = None,
        max_tokens_per_page: int = 2048
    ) -> list[SearchResult]:
        """
        使用 Search API 进行 Web 搜索
        
        API 端点: POST https://api.perplexity.ai/search
        
        Args:
            query: 搜索查询
            max_results: 结果数量 (1-20)
            country: 国家代码 (US/CN/GB/JP 等)
            language_filter: 语言过滤 (["en", "zh"] 等，最多10个)
            domain_filter: 域名过滤 (["techcrunch.com", "-reddit.com"] 等，最多20个)
            recency_filter: 时效性 ("day"/"week"/"month"/"year")
            max_tokens_per_page: 每页最大 token 数
            
        Returns:
            SearchResult 列表
        """
        if not self.api_key:
            return []
        
        print(f"  🔍 Perplexity Search: {query[:50]}...")
        
        payload = {
            "query": query,
            "max_results": min(max_results, 20),
            "max_tokens_per_page": max_tokens_per_page,
            "max_tokens": 25000
        }
        
        if country:
            payload["country"] = country
        if language_filter:
            payload["search_language_filter"] = language_filter[:10]
        if domain_filter:
            payload["search_domain_filter"] = domain_filter[:20]
        if recency_filter and recency_filter in ["day", "week", "month", "year"]:
            payload["search_recency_filter"] = recency_filter
        
        try:
            response = self._session.post(SEARCH_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    date=item.get("date"),
                    last_updated=item.get("last_updated")
                ))
            
            print(f"  ✅ Found {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Search Error: {e}")
            return []
        finally:
            self._rate_limit()
    
    def search_by_region(
        self,
        query: str,
        region: str,
        max_results: int = 10,
        **kwargs
    ) -> list[SearchResult]:
        """
        按地区搜索（自动设置国家/语言/时效性）
        
        Args:
            query: 搜索查询
            region: 地区代码 (us/cn/eu/jp/kr/sea)
            max_results: 结果数量
        """
        config = REGION_CONFIG.get(region, REGION_CONFIG["us"])
        return self.search(
            query,
            max_results=max_results,
            country=config.get("country"),
            language_filter=config.get("languages"),
            recency_filter=config.get("recency", "week"),
            **kwargs
        )
    
    # ════════════════════════════════════════════════════════════════════════════
    # Chat Completions API (第二步：分析内容)
    # ════════════════════════════════════════════════════════════════════════════
    
    def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Union[dict, list, str]:
        """
        使用 Sonar 模型分析内容
        
        API 端点: POST https://api.perplexity.ai/chat/completions
        
        Args:
            prompt: 完整 prompt (包含搜索结果和指令)
            model: 模型 (sonar/sonar-pro)
            temperature: 温度 (0-2，推荐 0.3 以获得稳定输出)
            max_tokens: 最大 token
            
        Returns:
            解析后的 JSON 或原始文本
        """
        if not self.api_key:
            return {}
        
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = self._session.post(CHAT_API_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            result_text = data['choices'][0]['message']['content']
            return self._extract_json(result_text)
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Analyze Error: {e}")
            return {}
        finally:
            self._rate_limit()
    
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
        region: str = "us",
        max_results: int = 10,
        **search_kwargs
    ) -> ExtractionResult:
        """
        搜索并提取产品信息（推荐方法）
        
        工作流程:
        1. Search API 获取搜索结果
        2. 格式化搜索结果
        3. Sonar 分析并提取产品
        
        Args:
            query: 搜索查询
            analysis_prompt: 分析 Prompt，需包含 {search_results} 占位符
            region: 地区代码
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
        
        print(f"    📊 Analyzing with Sonar...")
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
        }


# ════════════════════════════════════════════════════════════════════════════════
# 便捷函数（兼容旧 API）
# ════════════════════════════════════════════════════════════════════════════════

_default_client: Optional[PerplexityClient] = None


def get_client() -> PerplexityClient:
    """获取默认客户端（单例）"""
    global _default_client
    if _default_client is None:
        _default_client = PerplexityClient()
    return _default_client


def perplexity_search(query: str, max_results: int = 10, region: str = None, **kwargs) -> list[dict]:
    """
    快速搜索
    
    Returns:
        [{"title": "", "url": "", "content": ""}, ...]
    """
    client = get_client()
    if region:
        results = client.search_by_region(query, region, max_results, **kwargs)
    else:
        results = client.search(query, max_results=max_results, **kwargs)
    return [r.to_dict() for r in results]


def perplexity_analyze(prompt: str, **kwargs) -> Union[dict, list]:
    """快速分析"""
    client = get_client()
    return client.analyze(prompt, **kwargs)


# ════════════════════════════════════════════════════════════════════════════════
# 测试
# ════════════════════════════════════════════════════════════════════════════════

def test_client():
    """测试客户端"""
    print("\n" + "="*60)
    print("  🧪 Testing Perplexity Client")
    print("="*60)
    
    client = PerplexityClient()
    print(f"\n  Status: {client.get_status()}")
    
    if not client.is_available():
        print("\n  ❌ API key not set. Set PERPLEXITY_API_KEY env var.")
        return False
    
    # Test 1: 基础搜索
    print("\n  📍 Test 1: Basic Search")
    results = client.search("AI startup funding January 2026", max_results=3)
    if results:
        for i, r in enumerate(results, 1):
            print(f"    {i}. {r.title[:50]}...")
            print(f"       URL: {r.url}")
            print(f"       Date: {r.date}")
    else:
        print("    ❌ No results")
        return False
    
    # Test 2: 地区搜索
    print("\n  📍 Test 2: Regional Search (US)")
    results = client.search_by_region("AI startup", "us", max_results=3)
    if results:
        for i, r in enumerate(results, 1):
            print(f"    {i}. {r.title[:50]}...")
    else:
        print("    ❌ No results")
    
    # Test 3: 分析
    print("\n  📍 Test 3: Sonar Analysis")
    test_prompt = """Based on this search result, extract the company name and website:

### Linker Vision Raises US$35 Million Series-A
Source URL: https://www.prnewswire.com/news/linker-vision
Content: SANTA CLARA, Calif., Jan. 5, 2026 -- Linker Vision, a leading AI software platform company, announced Series A funding.

Return JSON format: {"name": "...", "website": "..."}"""
    
    analysis = client.analyze(test_prompt, temperature=0.1)
    print(f"    Result: {analysis}")
    
    print("\n  ✅ All tests passed!")
    return True


if __name__ == "__main__":
    test_client()
