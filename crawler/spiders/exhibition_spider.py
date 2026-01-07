"""
Exhibition products spider
Loads curated exhibitor products from a local JSON file.
"""

import json
import os
from typing import List, Dict, Any

from .base_spider import BaseSpider


class ExhibitionSpider(BaseSpider):
    """Local-file exhibition spider for CES/MWC/etc."""

    DATA_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'exhibitions')
    )
    LEGACY_FILE = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'exhibitions_products.json')
    )

    def crawl(self) -> List[Dict[str, Any]]:
        """Load exhibition products from local file."""
        data_files = self._get_data_files()
        if not data_files:
            print("  [Exhibitions] 数据文件不存在，跳过")
            return []

        products: List[Dict[str, Any]] = []
        for file_path in data_files:
            items = self._load_file(file_path)
            if not items:
                continue
            products.extend(self._parse_items(items, file_path))

        print(f"  [Exhibitions] 共获取 {len(products)} 个产品")
        return products

    def _get_data_files(self) -> List[str]:
        """Return all JSON files in DATA_DIR (fallback to legacy)."""
        data_files: List[str] = []
        if os.path.isdir(self.DATA_DIR):
            for entry in os.listdir(self.DATA_DIR):
                if not entry.endswith('.json'):
                    continue
                if entry.endswith('.sample.json'):
                    continue
                data_files.append(os.path.join(self.DATA_DIR, entry))

        if not data_files and os.path.exists(self.LEGACY_FILE):
            data_files.append(self.LEGACY_FILE)

        return sorted(data_files)

    def _load_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [Exhibitions] 读取数据失败: {file_path} -> {e}")
            return []

        if not isinstance(data, list):
            print(f"  [Exhibitions] 数据格式错误: {file_path}")
            return []

        return data

    def _parse_items(self, items: List[Dict[str, Any]], file_path: str) -> List[Dict[str, Any]]:
        products = []
        event_from_file = self._event_from_filename(file_path)

        for item in items:
            name = item.get('name')
            if not name:
                continue

            status = (item.get('status') or 'active').lower()
            if status not in ('active', 'published', 'live'):
                continue

            categories = item.get('categories') or ['other']
            is_hardware = 'hardware' in categories
            event_name = item.get('event') or event_from_file

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
                source='exhibition',
                extra={
                    'event': event_name,
                    'event_year': item.get('event_year') or item.get('year'),
                    'booth': item.get('booth', ''),
                    'brand': item.get('brand', ''),
                    'press_url': item.get('press_url', ''),
                    'release_year': item.get('release_year'),
                }
            )
            products.append(product)

        return products

    @staticmethod
    def _event_from_filename(file_path: str) -> str:
        filename = os.path.basename(file_path).split('.')[0].lower()
        mapping = {
            'ces': 'CES',
            'mwc': 'MWC',
            'ifa': 'IFA',
            'gtc': 'GTC',
        }
        return mapping.get(filename, filename.upper())
