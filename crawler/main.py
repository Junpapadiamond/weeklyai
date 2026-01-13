"""
WeeklyAI 爬虫主程序 - 增强版
自动采集 AI 产品信息并优化Logo和描述
"""

import os
import sys
import time
import json
import math
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spiders.github_spider import GitHubSpider
from spiders.huggingface_spider import HuggingFaceSpider
from spiders.product_hunt_spider import ProductHuntSpider
from spiders.hackernews_spider import HackerNewsSpider
from spiders.aitool_spider import AIToolSpider
from spiders.hardware_spider import AIHardwareSpider
from spiders.exhibition_spider import ExhibitionSpider
from spiders.company_spider import CompanySpider
from utils.image_utils import get_best_logo


class CrawlerManager:
    """爬虫管理器 - 增强版"""
    
    def __init__(self, use_db: bool = True):
        self.use_db = use_db
        self.db = None
        self.all_products = []
        
        if use_db:
            try:
                from database.db_handler import DatabaseHandler
                self.db = DatabaseHandler()
            except Exception as e:
                print(f"⚠ 数据库连接失败，将保存到本地文件: {e}")
                self.use_db = False
    
    def run_all_spiders(self) -> List[Dict[str, Any]]:
        """运行所有爬虫"""
        print("\n" + "=" * 60)
        print("🚀 WeeklyAI 爬虫开始运行 (增强版)")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_products = []
        stats = {
            'exhibition': 0,
            'company': 0,
            'github': 0,
            'huggingface': 0,
            'producthunt': 0,
            'hackernews': 0,
            'hardware': 0,
            'aitools': 0,
            'total': 0,
            'errors': []
        }
        
        # 1. 展会/发布会产品
        print("\n🏟️ [1/8] 展会产品库")
        print("-" * 40)
        try:
            spider = ExhibitionSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['exhibition'] = len(products)
            print(f"✓ 展会: 获取 {len(products)} 个产品")
        except Exception as e:
            stats['errors'].append(f"Exhibition: {str(e)}")
            print(f"✗ 展会爬取失败: {e}")

        # 2. 公司产品库
        print("\n🏢 [2/8] 公司产品库")
        print("-" * 40)
        try:
            spider = CompanySpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['company'] = len(products)
            print(f"✓ 公司: 获取 {len(products)} 个产品")
        except Exception as e:
            stats['errors'].append(f"Company: {str(e)}")
            print(f"✗ 公司爬取失败: {e}")

        # 3. AI 硬件产品
        print("\n🔧 [3/8] AI 硬件产品")
        print("-" * 40)
        try:
            spider = AIHardwareSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['hardware'] = len(products)
            print(f"✓ 硬件: 获取 {len(products)} 个产品")
        except Exception as e:
            stats['errors'].append(f"Hardware: {str(e)}")
            print(f"✗ 硬件爬取失败: {e}")
        
        # 4. GitHub Trending
        print("\n📦 [4/8] GitHub Trending AI 项目")
        print("-" * 40)
        try:
            spider = GitHubSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['github'] = len(products)
            print(f"✓ GitHub: 获取 {len(products)} 个项目")
        except Exception as e:
            stats['errors'].append(f"GitHub: {str(e)}")
            print(f"✗ GitHub 爬取失败: {e}")
        
        # 5. Hugging Face
        print("\n🤗 [5/8] Hugging Face 热门模型")
        print("-" * 40)
        try:
            spider = HuggingFaceSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['huggingface'] = len(products)
            print(f"✓ Hugging Face: 获取 {len(products)} 个模型/Spaces")
        except Exception as e:
            stats['errors'].append(f"HuggingFace: {str(e)}")
            print(f"✗ Hugging Face 爬取失败: {e}")
        
        # 6. ProductHunt
        print("\n🔥 [6/8] ProductHunt AI 产品")
        print("-" * 40)
        try:
            spider = ProductHuntSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['producthunt'] = len(products)
            print(f"✓ ProductHunt: 获取 {len(products)} 个产品")
        except Exception as e:
            stats['errors'].append(f"ProductHunt: {str(e)}")
            print(f"✗ ProductHunt 爬取失败: {e}")
        
        # 7. Hacker News
        print("\n🧠 [7/8] Hacker News 新发布")
        print("-" * 40)
        try:
            spider = HackerNewsSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['hackernews'] = len(products)
            print(f"✓ Hacker News: 获取 {len(products)} 个发布")
        except Exception as e:
            stats['errors'].append(f"HackerNews: {str(e)}")
            print(f"✗ Hacker News 爬取失败: {e}")

        # 8. AI 工具导航站
        print("\n🛠️ [8/8] AI 工具导航网站")
        print("-" * 40)
        try:
            spider = AIToolSpider()
            products = spider.crawl()
            all_products.extend(products)
            stats['aitools'] = len(products)
            print(f"✓ AI Tools: 获取 {len(products)} 个产品")
        except Exception as e:
            stats['errors'].append(f"AITools: {str(e)}")
            print(f"✗ AI Tools 爬取失败: {e}")
        
        # 数据处理
        print("\n🔄 处理数据...")
        print("  • 去重...")
        unique_products = self._deduplicate_products(all_products)
        print("  • 优化Logo...")
        enhanced_products = self._enhance_logos(unique_products)
        print("  • 更新历史/动量字段...")
        self._apply_history(enhanced_products)
        print("  • 计算排名...")
        ranked_products = self._calculate_rankings(enhanced_products)
        
        stats['total'] = len(ranked_products)
        self.all_products = ranked_products
        
        # 打印统计
        self._print_stats(stats)
        
        return ranked_products
    
    def _enhance_logos(self, products: List[Dict]) -> List[Dict]:
        """优化产品Logo"""
        enhanced = []
        
        for product in products:
            website = product.get('website', '')
            current_logo = product.get('logo_url', '')
            
            # 获取更好的Logo
            better_logo = get_best_logo(website, current_logo)
            product['logo_url'] = better_logo
            
            enhanced.append(product)
        
        return enhanced
    
    def _deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """去重产品"""
        seen = {}
        unique = []
        
        for product in products:
            # 使用名称的标准化版本作为key
            name_key = self._normalize_name(product['name'])
            
            if name_key in seen:
                # 合并信息：保留更高的分数和更完整的描述
                existing = seen[name_key]
                
                # 保留更长的描述
                if len(product.get('description', '')) > len(existing.get('description', '')):
                    existing['description'] = product['description']
                
                # 保留更好的Logo
                if product.get('logo_url') and not existing.get('logo_url'):
                    existing['logo_url'] = product['logo_url']
                
                # 保留更高的分数
                if product.get('trending_score', 0) > existing.get('trending_score', 0):
                    existing['trending_score'] = product['trending_score']
                
            else:
                seen[name_key] = product
                unique.append(product)
        
        return unique

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a product name for matching."""
        name_key = name.lower().strip()
        return ''.join(c for c in name_key if c.isalnum())

    @staticmethod
    def _history_key(product: Dict[str, Any]) -> str:
        """Stable key for history tracking."""
        name_key = CrawlerManager._normalize_name(product.get('name', ''))
        source = product.get('source', 'unknown') or 'unknown'
        return f"{name_key}:{source}"

    @staticmethod
    def _extract_metrics(product: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric metrics for growth tracking."""
        metrics = {}
        for key in ['weekly_users', 'trending_score', 'rating']:
            value = product.get(key)
            if isinstance(value, (int, float)):
                metrics[key] = float(value)
        extra = product.get('extra', {}) or {}
        for key, value in extra.items():
            if isinstance(value, (int, float)):
                metrics[key] = float(value)
        return metrics

    @staticmethod
    def _diff_metrics(current: Dict[str, float], previous: Dict[str, float]) -> Dict[str, float]:
        """Compute metric deltas."""
        deltas = {}
        for key, value in current.items():
            prev = previous.get(key, 0.0)
            delta = value - prev
            if delta != 0:
                deltas[key] = delta
        return deltas

    @staticmethod
    def _normalize_datetime(value: Any) -> str:
        """Normalize datetime-like values to ISO string."""
        if isinstance(value, datetime):
            return value.replace(microsecond=0).isoformat() + 'Z'
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value).replace(microsecond=0).isoformat() + 'Z'
        if isinstance(value, str):
            return value
        return ''

    @staticmethod
    def _parse_datetime(value: Any) -> Any:
        """Parse datetime-like values into datetime."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.endswith('Z'):
                cleaned = cleaned[:-1]
            try:
                parsed = datetime.fromisoformat(cleaned)
                if parsed.tzinfo:
                    parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return parsed
            except ValueError:
                return None
        return None

    def _load_history(self) -> Dict[str, Any]:
        """Load product history from local file."""
        history_file = os.path.join(os.path.dirname(__file__), 'data', 'products_history.json')
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_history(self, history: Dict[str, Any]) -> None:
        """Persist product history to local file."""
        history_file = os.path.join(os.path.dirname(__file__), 'data', 'products_history.json')
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _apply_history(self, products: List[Dict[str, Any]]) -> None:
        """Annotate products with first_seen/last_seen and metric deltas."""
        history = self._load_history()
        now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

        for product in products:
            key = self._history_key(product)
            entry = history.get(key, {})

            first_seen = entry.get('first_seen') or now_iso
            product['first_seen'] = first_seen
            product['last_seen'] = now_iso

            published_at = product.get('published_at') or product.get('extra', {}).get('published_at')
            if published_at:
                normalized = self._normalize_datetime(published_at)
                if normalized:
                    product['published_at'] = normalized

            metrics = self._extract_metrics(product)
            previous_metrics = entry.get('last_metrics', {}) or {}
            metric_delta = self._diff_metrics(metrics, previous_metrics)
            if metric_delta:
                extra = product.get('extra', {}) or {}
                extra['metrics_delta'] = metric_delta
                product['extra'] = extra

            history_entry = {
                'first_seen': first_seen,
                'last_seen': now_iso,
                'last_metrics': metrics,
                'metrics_history': entry.get('metrics_history', []),
            }
            history_entry['metrics_history'].append({
                'seen_at': now_iso,
                'metrics': metrics
            })
            history_entry['metrics_history'] = history_entry['metrics_history'][-30:]
            history[key] = history_entry

        self._save_history(history)
    
    def _calculate_rankings(self, products: List[Dict]) -> List[Dict]:
        """计算热度排名 (Hot + Top)"""
        current_year = datetime.now().year

        source_stats = self._build_source_stats(products)

        for product in products:
            scores = self._score_product(product, current_year, source_stats)
            product['hot_score'] = scores['hot_score']
            product['top_score'] = scores['top_score']
            product['final_score'] = product['top_score']

        # 按 Top Score 排序作为默认输出
        products.sort(key=lambda x: x.get('top_score', x.get('final_score', 0)), reverse=True)

        return products

    @staticmethod
    def _log_scale(value: float, cap: float = 6.0) -> float:
        """Log-scale normalization to 0-1."""
        if not value or value <= 0:
            return 0.0
        return min(1.0, math.log10(1 + value) / cap)

    @staticmethod
    def _relative_log(value: float, max_value: float) -> float:
        """Normalize value within a source using log scale."""
        if not value or value <= 0:
            return 0.0
        if not max_value or max_value <= 0:
            return 0.0
        return min(1.0, math.log10(1 + value) / math.log10(1 + max_value))

    def _build_source_stats(self, products: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Compute per-source metric maxima for normalization."""
        stats: Dict[str, Dict[str, float]] = {}

        for product in products:
            source = product.get('source', 'unknown')
            extra = product.get('extra', {}) or {}
            weekly_users = product.get('weekly_users', 0) or 0
            downloads = extra.get('downloads', 0) or 0
            volume_metric = max(weekly_users, downloads)

            if source not in stats:
                stats[source] = {
                    'max_volume': 0,
                    'max_stars': 0,
                    'max_forks': 0,
                    'max_votes': 0,
                    'max_likes': 0,
                }

            stats[source]['max_volume'] = max(stats[source]['max_volume'], volume_metric)
            stats[source]['max_stars'] = max(stats[source]['max_stars'], extra.get('stars', 0) or 0)
            stats[source]['max_forks'] = max(stats[source]['max_forks'], extra.get('forks', 0) or 0)
            stats[source]['max_votes'] = max(stats[source]['max_votes'], extra.get('votes', 0) or 0)
            stats[source]['max_likes'] = max(stats[source]['max_likes'], extra.get('likes', 0) or 0)

        return stats

    def _score_product(self, product: Dict, current_year: int, source_stats: Dict[str, Dict[str, float]]) -> Dict[str, int]:
        """多维度评分 (动量/质量/互动/规模/新鲜度)."""
        extra = product.get('extra', {}) or {}

        # Volume: weekly users or downloads
        weekly_users = product.get('weekly_users', 0) or 0
        downloads = extra.get('downloads', 0) or 0
        volume_metric = max(weekly_users, downloads)
        source = product.get('source', 'unknown')
        source_meta = source_stats.get(source, {})
        volume_score = self._relative_log(volume_metric, source_meta.get('max_volume', 0)) or self._log_scale(volume_metric)

        # Engagement: stars/forks/votes/likes (weighted)
        engagement_weights = {
            'stars': 0.45,
            'forks': 0.15,
            'votes': 0.25,
            'likes': 0.15,
        }
        engagement_score = 0.0
        weight_sum = 0.0
        for key, weight in engagement_weights.items():
            value = extra.get(key, 0) or 0
            if value > 0:
                max_key = f"max_{key}"
                rel = self._relative_log(value, source_meta.get(max_key, 0))
                metric_score = rel if rel > 0 else self._log_scale(value)
                engagement_score += metric_score * weight
                weight_sum += weight
        if weight_sum > 0:
            engagement_score = engagement_score / weight_sum

        # Quality: rating 0-5
        rating = product.get('rating', 0) or 0
        quality_score = min(1.0, rating / 5.0)

        # Momentum: base trend + growth deltas
        momentum_score = min(1.0, (product.get('trending_score', 0) or 0) / 100.0)
        growth_score = 0.0
        metric_delta = extra.get('metrics_delta', {}) or {}
        if metric_delta:
            growth_keys = ['stars', 'votes', 'likes', 'downloads', 'weekly_users', 'points', 'comments']
            positive_sum = sum(max(0, metric_delta.get(k, 0)) for k in growth_keys)
            if positive_sum > 0:
                growth_score = min(1.0, math.log10(1 + positive_sum) / 4.0)
                momentum_score = (0.65 * momentum_score) + (0.35 * growth_score)

        # Recency: published_at/first_seen or release year
        recency_score = 0.55
        published_at = product.get('published_at') or extra.get('published_at') or product.get('first_seen')
        parsed = self._parse_datetime(published_at) if published_at else None
        if parsed:
            days = max(0, (datetime.utcnow() - parsed).days)
            if days <= 7:
                recency_score = 1.0
            elif days <= 30:
                recency_score = 0.85
            elif days <= 90:
                recency_score = 0.7
            elif days <= 180:
                recency_score = 0.6
            elif days <= 365:
                recency_score = 0.5
            else:
                recency_score = 0.4
        else:
            release_year = product.get('release_year') or extra.get('release_year')
            if release_year:
                year_gap = max(0, current_year - int(release_year))
                if year_gap == 0:
                    recency_score = 1.0
                elif year_gap == 1:
                    recency_score = 0.8
                elif year_gap == 2:
                    recency_score = 0.6
                else:
                    recency_score = 0.4

        # Source bonus (small bias for curated sources)
        source_bonus_map = {
            'producthunt': 0.08,
            'producthunt_curated': 0.1,
            'github': 0.05,
            'huggingface': 0.04,
            'hackernews': 0.04,
            'ai_hardware': 0.06,
            'exhibition': 0.08,
            'aitools': 0.03,
            'toolify': 0.03,
        }
        source_bonus = source_bonus_map.get(product.get('source', ''), 0.02)
        if product.get('is_hardware', False):
            source_bonus += 0.03

        hot_score = (
            0.50 * momentum_score +
            0.20 * recency_score +
            0.12 * engagement_score +
            0.08 * quality_score +
            0.10 * volume_score +
            source_bonus
        )
        top_score = (
            0.35 * volume_score +
            0.22 * quality_score +
            0.18 * engagement_score +
            0.15 * momentum_score +
            0.10 * recency_score +
            source_bonus
        )

        return {
            'hot_score': min(100, int(hot_score * 100)),
            'top_score': min(100, int(top_score * 100)),
        }
    
    def _print_stats(self, stats: Dict):
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("📊 采集统计")
        print("=" * 60)
        print(f"  • 展会产品:     {stats['exhibition']:4d} 个产品")
        print(f"  • 公司产品:     {stats['company']:4d} 个产品")
        print(f"  • AI 硬件:      {stats['hardware']:4d} 个产品")
        print(f"  • GitHub:       {stats['github']:4d} 个项目")
        print(f"  • Hugging Face: {stats['huggingface']:4d} 个模型")
        print(f"  • ProductHunt:  {stats['producthunt']:4d} 个产品")
        print(f"  • Hacker News:  {stats['hackernews']:4d} 个发布")
        print(f"  • AI Tools:     {stats['aitools']:4d} 个工具")
        print("-" * 40)
        print(f"  ✓ 总计 (去重后): {stats['total']:4d} 个产品")
        
        if stats['errors']:
            print("\n⚠ 错误:")
            for error in stats['errors']:
                print(f"  • {error}")
        
        print("=" * 60)
    
    def save_to_database(self):
        """保存到数据库"""
        if not self.all_products:
            print("没有数据可保存")
            return
        
        if self.db:
            try:
                saved = self.db.save_products(self.all_products)
                print(f"✓ 已保存 {saved} 条记录到数据库")
            except Exception as e:
                print(f"✗ 数据库保存失败: {e}")
                self._save_to_file()
        else:
            self._save_to_file()
    
    def _save_to_file(self):
        """保存到本地 JSON 文件"""
        output_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'products_{timestamp}.json')
        latest_file = os.path.join(output_dir, 'products_latest.json')
        
        data = []
        for product in self.all_products:
            item = {k: v for k, v in product.items() 
                   if not callable(v) and k != '_id'}
            if 'created_at' in item:
                item['created_at'] = str(item['created_at'])
            if 'updated_at' in item:
                item['updated_at'] = str(item['updated_at'])
            data.append(item)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已保存到 {filename}")
        print(f"✓ 已更新 {latest_file}")
    
    def get_top_products(self, n: int = 15) -> List[Dict]:
        """获取热度最高的 n 个产品"""
        return self.all_products[:n]
    
    def close(self):
        """清理资源"""
        if self.db:
            self.db.close()


def main():
    parser = argparse.ArgumentParser(
        description='WeeklyAI 爬虫 - 采集全球热门 AI 产品 (增强版)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--no-db', action='store_true', help='不使用数据库')
    parser.add_argument('--top', type=int, default=0, help='显示Top N产品')
    parser.add_argument('--interval-hours', type=float, default=0, help='每隔多少小时运行一次 (0=只运行一次)')
    
    args = parser.parse_args()

    def run_job():
        manager = CrawlerManager(use_db=not args.no_db)
        try:
            products = manager.run_all_spiders()
            manager.save_to_database()

            if args.top > 0:
                print(f"\n🏆 热度 Top {args.top}:")
                print("-" * 70)
                top_products = manager.get_top_products(args.top)
                for i, p in enumerate(top_products, 1):
                    score = p.get('top_score', p.get('final_score', p.get('trending_score', 0)))
                    hw_tag = " [硬件]" if p.get('is_hardware') else ""
                    print(f"  {i:2d}. {p['name']:<30} 分数:{score:3d}  {p.get('source', 'N/A'):<15}{hw_tag}")

            print("\n✅ 爬虫任务完成!")

        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断")
            raise
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            manager.close()

    if args.interval_hours and args.interval_hours > 0:
        print(f"⏲ 定时模式: 每 {args.interval_hours} 小时运行一次")
        while True:
            run_job()
            time.sleep(args.interval_hours * 3600)
    else:
        run_job()


if __name__ == "__main__":
    main()
