"""
GitHub 爬虫 - 增强版
获取更完整的项目信息，包括README、Logo等
"""

import re
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_spider import BaseSpider


class GitHubSpider(BaseSpider):
    """GitHub Trending 爬虫 - 增强版"""
    
    BASE_URL = "https://github.com"
    API_BASE = "https://api.github.com"
    
    def __init__(self):
        super().__init__()
        # 可选: 添加 GitHub Token 提高 API 限制
        self.github_token = None  # os.getenv('GITHUB_TOKEN')
        if self.github_token:
            self.session.headers['Authorization'] = f'token {self.github_token}'
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 GitHub AI 项目"""
        products = []
        seen_repos = set()
        
        print("  [GitHub] 爬取 AI 项目...")
        
        # 1. Trending AI 项目
        trending_repos = self._get_trending_ai_repos()
        for repo in trending_repos:
            if repo['name'] not in seen_repos:
                products.append(repo)
                seen_repos.add(repo['name'])
        
        print(f"  [GitHub] 共获取 {len(products)} 个 AI 项目")
        return products
    
    def _get_trending_ai_repos(self) -> List[Dict[str, Any]]:
        """获取 Trending AI 仓库"""
        products = []
        
        # 使用 GitHub API 搜索热门 AI 项目
        ai_queries = [
            "artificial intelligence stars:>5000",
            "machine learning stars:>5000",
            "deep learning stars:>3000",
            "llm language:python stars:>1000",
            "gpt chatbot stars:>1000",
        ]
        
        for query in ai_queries[:3]:  # 限制查询数
            try:
                repos = self._search_repos_api(query, per_page=10)
                
                for repo_data in repos:
                    try:
                        product = self._parse_repo_detailed(repo_data)
                        if product:
                            products.append(product)
                        time.sleep(0.5)  # 避免触发限流
                    except:
                        continue
                
            except Exception as e:
                print(f"    ⚠ 搜索 '{query}' 失败: {e}")
                continue
        
        return products
    
    def _search_repos_api(self, query: str, per_page: int = 10) -> List[Dict]:
        """使用 GitHub API 搜索仓库"""
        url = f"{self.API_BASE}/search/repositories"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page
        }
        
        response = self.session.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        
        return []
    
    def _parse_repo_detailed(self, repo: Dict) -> Optional[Dict[str, Any]]:
        """解析仓库详细信息"""
        full_name = repo.get('full_name', '')
        if not full_name:
            return None
        
        owner, name = full_name.split('/')
        
        # 获取完整描述
        description = repo.get('description', '')
        
        # 如果描述太短，尝试从 README 获取
        if len(description) < 50:
            readme_desc = self._get_readme_description(full_name)
            if readme_desc:
                description = readme_desc
        
        # 获取统计数据
        stars = repo.get('stargazers_count', 0)
        forks = repo.get('forks_count', 0)
        watchers = repo.get('watchers_count', 0)
        
        # 获取 Logo（GitHub 头像）
        logo_url = repo.get('owner', {}).get('avatar_url', '')
        
        # 获取语言
        language = repo.get('language', '')
        
        # 获取主题/话题
        topics = repo.get('topics', [])
        
        # 推断分类
        categories = self._infer_categories_from_repo(description, name, topics, language)
        
        # 计算热度分数
        trending_score = self._calculate_trending_score(stars, forks, watchers)
        
        # 生成更详细的描述
        enhanced_description = self._generate_description(name, description, stars, topics)
        
        return self.create_product(
            name=name,
            description=enhanced_description,
            logo_url=logo_url,
            website=repo.get('html_url', ''),
            categories=categories if categories else ['coding'],
            rating=min(5.0, 4.0 + stars / 50000),
            weekly_users=stars // 10,  # 估算
            trending_score=trending_score,
            source='github',
            extra={
                'stars': stars,
                'forks': forks,
                'language': language,
                'topics': topics[:5],
                'owner': owner,
            }
        )
    
    def _get_readme_description(self, full_name: str) -> str:
        """从 README 获取项目描述"""
        try:
            url = f"{self.API_BASE}/repos/{full_name}/readme"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # 获取 README 内容 URL
                download_url = data.get('download_url', '')
                if download_url:
                    readme_response = self.session.get(download_url, timeout=5)
                    if readme_response.status_code == 200:
                        readme_text = readme_response.text
                        
                        # 提取第一段有效描述
                        lines = readme_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # 跳过标题、图片、链接等
                            if (line and 
                                not line.startswith('#') and 
                                not line.startswith('!') and 
                                not line.startswith('[') and
                                len(line) > 30):
                                return line[:200]
        except:
            pass
        
        return ''
    
    def _generate_description(self, name: str, desc: str, stars: int, topics: List) -> str:
        """生成增强的描述"""
        parts = []
        
        # 基础描述
        if desc:
            parts.append(desc)
        else:
            parts.append(f"GitHub 项目: {name}")
        
        # 添加热度信息
        if stars > 10000:
            parts.append(f"⭐ {stars // 1000}K+ Stars")
        elif stars > 1000:
            parts.append(f"⭐ {stars // 100}00+ Stars")
        
        # 添加主要标签
        if topics:
            relevant_topics = [t for t in topics if t in [
                'ai', 'machine-learning', 'deep-learning', 'nlp', 
                'computer-vision', 'llm', 'gpt', 'chatgpt'
            ]]
            if relevant_topics:
                parts.append(f"技术: {', '.join(relevant_topics[:2])}")
        
        return ' | '.join(parts)
    
    def _infer_categories_from_repo(self, desc: str, name: str, 
                                     topics: List, language: str) -> List[str]:
        """从仓库信息推断分类"""
        text = f"{desc} {name} {' '.join(topics)}".lower()
        categories = set()
        
        keyword_mapping = {
            'coding': ['code', 'developer', 'ide', 'copilot', 'programming', 
                      'compiler', 'debugger', 'vscode', 'jupyter'],
            'image': ['image', 'vision', 'cv', 'diffusion', 'stable-diffusion',
                     'gan', 'style-transfer', 'object-detection', 'segmentation'],
            'video': ['video', 'animation', 'motion', 'video-generation'],
            'voice': ['speech', 'audio', 'tts', 'stt', 'voice', 'whisper',
                     'asr', 'sound', 'music'],
            'writing': ['nlp', 'text', 'language', 'translation', 'summarization',
                       'chatbot', 'dialogue'],
        }
        
        for category, keywords in keyword_mapping.items():
            if any(kw in text for kw in keywords):
                categories.add(category)
        
        # LLM 相关通常归到 coding
        if any(kw in text for kw in ['llm', 'gpt', 'bert', 'transformer', 'language-model']):
            categories.add('coding')
        
        return list(categories) if categories else ['coding']
    
    def _calculate_trending_score(self, stars: int, forks: int, watchers: int) -> int:
        """计算热度分数"""
        score = 0
        
        # Stars 权重最高
        if stars > 50000:
            score += 40
        elif stars > 20000:
            score += 35
        elif stars > 10000:
            score += 30
        elif stars > 5000:
            score += 25
        elif stars > 1000:
            score += 20
        else:
            score += 15
        
        # Forks
        if forks > 10000:
            score += 25
        elif forks > 5000:
            score += 20
        elif forks > 1000:
            score += 15
        else:
            score += 10
        
        # Watchers
        if watchers > 1000:
            score += 15
        elif watchers > 500:
            score += 10
        else:
            score += 5
        
        return min(100, score)
