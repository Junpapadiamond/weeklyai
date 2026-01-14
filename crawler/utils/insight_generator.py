"""
AI Insight Generator - 使用 Claude API 生成产品洞察
为每个产品自动生成 "为什么 PM 应该关注" 的分析
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

# Claude API
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("  ⚠ anthropic package not installed. Run: pip install anthropic")

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'insight_cache')


class InsightGenerator:
    """AI 洞察生成器 - 使用 Claude API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.cache = {}
        self._load_cache()

        if HAS_ANTHROPIC and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print("  ✓ Insight Generator initialized with Claude API")
        else:
            print("  ⚠ Insight Generator running in fallback mode (no API)")

    def _get_cache_key(self, product: Dict[str, Any]) -> str:
        """生成产品的缓存key"""
        name = product.get('name', '')
        desc = product.get('description', '')[:200]
        content = f"{name}|{desc}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_cache(self):
        """加载缓存"""
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, 'insights.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"  ✓ Loaded {len(self.cache)} cached insights")
            except Exception:
                self.cache = {}

    def _save_cache(self):
        """保存缓存"""
        cache_file = os.path.join(CACHE_DIR, 'insights.json')
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠ Failed to save cache: {e}")

    def generate_insight(self, product: Dict[str, Any]) -> Optional[str]:
        """为单个产品生成洞察

        Args:
            product: 产品信息字典，包含 name, description, categories 等

        Returns:
            PM 视角的产品洞察，1-2句话
        """
        # 检查缓存
        cache_key = self._get_cache_key(product)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 如果已有 why_matters 且非空，直接使用
        existing = product.get('why_matters', '').strip()
        if existing and len(existing) > 10:
            self.cache[cache_key] = existing
            return existing

        # 如果没有API客户端，使用规则生成
        if not self.client:
            insight = self._generate_fallback_insight(product)
            self.cache[cache_key] = insight
            return insight

        # 使用 Claude API 生成
        try:
            insight = self._call_claude_api(product)
            if insight:
                self.cache[cache_key] = insight
                self._save_cache()
                return insight
        except Exception as e:
            print(f"  ⚠ Claude API error for {product.get('name')}: {e}")

        # 失败时使用规则生成
        insight = self._generate_fallback_insight(product)
        self.cache[cache_key] = insight
        return insight

    def _call_claude_api(self, product: Dict[str, Any]) -> Optional[str]:
        """调用 Claude API 生成洞察"""
        name = product.get('name', 'Unknown')
        description = product.get('description', '')[:500]
        categories = ', '.join(product.get('categories', []))
        funding = product.get('funding_total', '')
        users = product.get('weekly_users', 0)

        prompt = f"""你是一位资深 AI 产品经理分析师。请用中文，用1-2句话简洁说明：一个产品经理为什么应该关注这个产品？

产品名称: {name}
产品描述: {description}
分类: {categories}
{f'融资: {funding}' if funding else ''}
{f'周活用户: {users:,}' if users else ''}

要求:
- 直接说要点，不要废话
- 突出产品的创新点或商业潜力
- 从 PM 视角分析其价值
- 中文回答，不超过80字"""

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )

        if response.content:
            return response.content[0].text.strip()
        return None

    def _generate_fallback_insight(self, product: Dict[str, Any]) -> str:
        """规则生成洞察（无API时使用）"""
        name = product.get('name', 'Unknown')
        categories = product.get('categories', [])
        funding = product.get('funding_total', '')
        users = product.get('weekly_users', 0)
        source = product.get('source', '')
        dark_horse_index = product.get('dark_horse_index', 0)

        insights = []

        # 基于融资
        if funding:
            if 'Series' in funding or '$' in funding:
                insights.append(f"刚完成{funding}融资，资本认可度高")

        # 基于用户规模
        if users:
            if users < 10000:
                insights.append("早期产品，处于快速增长期")
            elif users < 100000:
                insights.append("用户基础稳健，产品已验证")
            else:
                insights.append(f"周活{users//1000}K+，已形成规模")

        # 基于黑马指数
        if dark_horse_index >= 4:
            insights.append("高潜力新星，值得提前布局")

        # 基于来源
        if source == 'producthunt':
            insights.append("PH热门，社区关注度高")
        elif source == 'hackernews':
            insights.append("技术圈热议，开发者认可")

        # 基于分类
        category_insights = {
            'coding': '开发效率工具，提升团队产能',
            'image': '视觉创作利器，内容生产新选择',
            'video': '视频生成能力，多媒体新趋势',
            'voice': '语音技术突破，交互方式革新',
            'hardware': '硬件+AI融合，新形态产品',
            'education': '教育场景落地，市场潜力大',
            'healthcare': '医疗AI应用，高壁垒赛道',
            'finance': '金融科技应用，合规性要求高',
        }
        for cat in categories:
            if cat in category_insights:
                insights.append(category_insights[cat])
                break

        if insights:
            return '；'.join(insights[:2]) + '。'

        return f"{name}是一个新兴AI产品，值得关注其后续发展。"

    def batch_generate(self, products: list, max_api_calls: int = 50) -> list:
        """批量生成洞察

        Args:
            products: 产品列表
            max_api_calls: 最大API调用次数（控制成本）

        Returns:
            添加了 why_matters 字段的产品列表
        """
        api_calls = 0

        for i, product in enumerate(products):
            # 检查是否已有洞察
            if product.get('why_matters'):
                continue

            # 生成洞察
            cache_key = self._get_cache_key(product)
            is_cached = cache_key in self.cache

            insight = self.generate_insight(product)
            if insight:
                product['why_matters'] = insight

            # 统计API调用
            if not is_cached and self.client:
                api_calls += 1
                if api_calls >= max_api_calls:
                    print(f"  ⚠ Reached API limit ({max_api_calls}), remaining products use fallback")
                    self.client = None  # 切换到fallback模式

            if (i + 1) % 10 == 0:
                print(f"  → Generated insights for {i + 1}/{len(products)} products")

        # 保存缓存
        self._save_cache()
        print(f"  ✓ Generated insights for {len(products)} products ({api_calls} API calls)")

        return products


# 便捷函数
def generate_insights_for_products(products: list, api_key: Optional[str] = None) -> list:
    """为产品列表生成洞察的便捷函数"""
    generator = InsightGenerator(api_key)
    return generator.batch_generate(products)
