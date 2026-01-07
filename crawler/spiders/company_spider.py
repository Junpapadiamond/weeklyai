"""
Company products spider
Loads curated company product lists from local JSON files.
"""

import json
import os
from typing import List, Dict, Any

from .base_spider import BaseSpider


class CompanySpider(BaseSpider):
    """Local-file spider for company AI product lists."""

    DATA_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'companies')
    )

    def crawl(self) -> List[Dict[str, Any]]:
        if not os.path.isdir(self.DATA_DIR):
            print("  [Companies] 数据目录不存在，跳过")
            return []

        products: List[Dict[str, Any]] = []
        for entry in sorted(os.listdir(self.DATA_DIR)):
            if not entry.endswith('.json') or entry.endswith('.sample.json'):
                continue
            file_path = os.path.join(self.DATA_DIR, entry)
            items = self._load_file(file_path)
            if not items:
                continue
            products.extend(self._parse_items(items, file_path))

        print(f"  [Companies] 共获取 {len(products)} 个产品")
        return products

    def _load_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [Companies] 读取数据失败: {file_path} -> {e}")
            return []

        if not isinstance(data, list):
            print(f"  [Companies] 数据格式错误: {file_path}")
            return []

        return data

    def _parse_items(self, items: List[Dict[str, Any]], file_path: str) -> List[Dict[str, Any]]:
        products = []
        company_name = os.path.basename(file_path).split('.')[0].upper()

        for item in items:
            name = item.get('name')
            if not name:
                continue

            status = (item.get('status') or 'active').lower()
            if status not in ('active', 'published', 'live'):
                continue

            categories = item.get('categories') or ['other']
            is_hardware = 'hardware' in categories

            product = self.create_product(
                name=name,
                description=item.get('description', ''),
                logo_url=item.get('logo_url', ''),
                website=item.get('website', ''),
                categories=categories,
                rating=item.get('rating', 0),
                weekly_users=item.get('weekly_users', 0),
                trending_score=item.get('trending_score', 0),
                is_hardware=is_hardware,
                source='company',
                extra={
                    'brand': item.get('brand', company_name),
                    'press_url': item.get('press_url', ''),
                    'release_year': item.get('release_year'),
                    'company': company_name,
                }
            )
            products.append(product)

        return products
