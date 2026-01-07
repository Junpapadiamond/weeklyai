"""
爬虫工具函数
包括 Logo 获取、图片下载等功能
"""

import requests
import hashlib
from typing import Optional
from urllib.parse import urlparse


class ImageFetcher:
    """图片获取工具"""
    
    @staticmethod
    def get_logo_url(website: str, name: str = '') -> str:
        """
        智能获取网站Logo
        
        尝试多种方法:
        1. Favicon (最常用)
        2. Apple Touch Icon
        3. OpenGraph Image
        4. Clearbit Logo API
        5. Google S2 (网站截图)
        """
        if not website:
            return ''
        
        try:
            domain = urlparse(website).netloc
            if not domain:
                return ''
            
            # 方法1: Clearbit Logo API (最可靠)
            clearbit_url = f"https://logo.clearbit.com/{domain}"
            if ImageFetcher._check_url_exists(clearbit_url):
                return clearbit_url
            
            # 方法2: Google Favicon Service
            google_favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
            return google_favicon
            
        except:
            return ''
    
    @staticmethod
    def _check_url_exists(url: str, timeout: int = 2) -> bool:
        """检查URL是否可访问"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_favicon(website: str) -> str:
        """获取网站 Favicon"""
        try:
            domain = urlparse(website).netloc
            if not domain:
                return ''
            
            # 标准 favicon 路径
            favicon_urls = [
                f"https://{domain}/favicon.ico",
                f"https://{domain}/favicon.png",
                f"https://{domain}/apple-touch-icon.png",
                f"https://{domain}/apple-touch-icon-precomposed.png",
            ]
            
            for url in favicon_urls:
                if ImageFetcher._check_url_exists(url):
                    return url
            
            # 使用 Google S2
            return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
            
        except:
            return ''
    
    @staticmethod
    def enhance_logo_url(existing_url: str, website: str) -> str:
        """
        增强已有的 Logo URL
        如果现有URL不存在或质量不高，尝试获取更好的
        """
        if not existing_url or 'huggingface' in existing_url:
            # 尝试获取更好的Logo
            new_url = ImageFetcher.get_logo_url(website)
            if new_url:
                return new_url
        
        return existing_url


# 常用网站Logo映射（高质量）
LOGO_OVERRIDES = {
    'openai.com': 'https://cdn.openai.com/common/images/favicon.ico',
    'chat.openai.com': 'https://cdn.openai.com/common/images/favicon.ico',
    'anthropic.com': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
    'claude.ai': 'https://www.anthropic.com/images/icons/apple-touch-icon.png',
    'github.com': 'https://github.githubassets.com/favicons/favicon.png',
    'huggingface.co': 'https://huggingface.co/front/assets/huggingface_logo-noborder.svg',
    'google.com': 'https://www.google.com/favicon.ico',
    'microsoft.com': 'https://www.microsoft.com/favicon.ico',
    'meta.com': 'https://static.xx.fbcdn.net/rsrc.php/yb/r/hLRJ1GG_y0J.ico',
    'apple.com': 'https://www.apple.com/favicon.ico',
    'nvidia.com': 'https://www.nvidia.com/favicon.ico',
    'stability.ai': 'https://stability.ai/favicon.ico',
    'midjourney.com': 'https://www.midjourney.com/apple-touch-icon.png',
    'runwayml.com': 'https://runwayml.com/favicon.ico',
    'lg.com': 'https://www.lg.com/favicon.ico',
    'tcl.com': 'https://www.tcl.com/favicon.ico',
    'asus.com': 'https://www.asus.com/favicon.ico',
}


def get_best_logo(website: str, current_logo: str = '') -> str:
    """
    获取最佳质量的Logo
    
    Args:
        website: 网站URL
        current_logo: 当前已有的Logo URL
    
    Returns:
        最佳Logo URL
    """
    if not website:
        return current_logo or ''
    
    try:
        domain = urlparse(website).netloc.replace('www.', '')
        
        # 1. 检查预定义映射
        if domain in LOGO_OVERRIDES:
            return LOGO_OVERRIDES[domain]
        
        # 2. 如果当前Logo存在且不是默认图标，保留
        if current_logo and current_logo != '' and 'huggingface_logo' not in current_logo:
            return current_logo
        
        # 3. 尝试智能获取
        logo_url = ImageFetcher.get_logo_url(website)
        if logo_url:
            return logo_url
        
        # 4. 返回当前或空
        return current_logo or ''
        
    except:
        return current_logo or ''

