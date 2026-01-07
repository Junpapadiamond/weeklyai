"""
爬虫基类
"""

import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any


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
    
    @abstractmethod
    def crawl(self) -> List[Dict[str, Any]]:
        """
        执行爬取操作
        返回产品列表
        """
        pass
    
    def fetch(self, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        """
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
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
        if 'release_year' in kwargs and 'release_year' not in extra:
            extra['release_year'] = kwargs.get('release_year')
        if 'price' in kwargs and 'price' not in extra:
            extra['price'] = kwargs.get('price')
        if extra:
            product['extra'] = extra
            if 'release_year' in extra:
                product['release_year'] = extra['release_year']
            if 'price' in extra:
                product['price'] = extra['price']

        return product


