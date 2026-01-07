"""
Hugging Face 爬虫
爬取 Hugging Face 上热门的 AI 模型和 Spaces
"""

import json
from typing import List, Dict, Any
from .base_spider import BaseSpider


class HuggingFaceSpider(BaseSpider):
    """Hugging Face 爬虫"""
    
    # Hugging Face API 端点
    API_BASE = "https://huggingface.co/api"
    WEB_BASE = "https://huggingface.co"
    
    # 模型类型到分类的映射
    PIPELINE_CATEGORIES = {
        'text-generation': 'writing',
        'text2text-generation': 'writing',
        'summarization': 'writing',
        'translation': 'writing',
        'conversational': 'writing',
        'text-classification': 'other',
        'token-classification': 'other',
        'question-answering': 'other',
        'fill-mask': 'other',
        'sentence-similarity': 'other',
        'feature-extraction': 'coding',
        'image-classification': 'image',
        'object-detection': 'image',
        'image-segmentation': 'image',
        'image-to-text': 'image',
        'text-to-image': 'image',
        'image-to-image': 'image',
        'automatic-speech-recognition': 'voice',
        'text-to-speech': 'voice',
        'audio-classification': 'voice',
        'audio-to-audio': 'voice',
        'video-classification': 'video',
        'text-to-video': 'video',
        'zero-shot-classification': 'other',
        'zero-shot-image-classification': 'image',
        'reinforcement-learning': 'coding',
    }
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取 Hugging Face 热门模型和 Spaces"""
        products = []
        
        # 1. 获取热门模型
        print("  [HuggingFace] 获取热门模型...")
        try:
            models = self._get_trending_models()
            products.extend(models)
            print(f"    ✓ 获取到 {len(models)} 个热门模型")
        except Exception as e:
            print(f"    ✗ 获取模型失败: {e}")
        
        # 2. 获取热门 Spaces
        print("  [HuggingFace] 获取热门 Spaces...")
        try:
            spaces = self._get_trending_spaces()
            products.extend(spaces)
            print(f"    ✓ 获取到 {len(spaces)} 个热门 Spaces")
        except Exception as e:
            print(f"    ✗ 获取 Spaces 失败: {e}")
        
        print(f"  [HuggingFace] 共获取 {len(products)} 个产品")
        return products
    
    def _get_trending_models(self, limit: int = 30) -> List[Dict[str, Any]]:
        """获取热门模型"""
        # 使用 Hugging Face API 获取热门模型
        url = f"{self.API_BASE}/models"
        params = {
            'sort': 'trending',
            'limit': limit,
            'full': 'true'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            models_data = response.json()
        except Exception as e:
            # 备用方案：获取下载量最多的模型
            params['sort'] = 'downloads'
            response = self.session.get(url, params=params, timeout=30)
            models_data = response.json()
        
        products = []
        
        for model in models_data:
            try:
                product = self._parse_model(model)
                if product:
                    products.append(product)
            except Exception as e:
                continue
        
        return products
    
    def _parse_model(self, model: Dict) -> Dict[str, Any]:
        """解析模型数据"""
        model_id = model.get('id', '')
        if not model_id:
            return None
        
        # 模型名称（取最后一部分）
        name = model_id.split('/')[-1] if '/' in model_id else model_id
        
        # 获取下载量和点赞
        downloads = model.get('downloads', 0)
        likes = model.get('likes', 0)
        
        # 获取 pipeline 类型
        pipeline_tag = model.get('pipeline_tag', '')
        
        # 推断分类
        categories = []
        if pipeline_tag and pipeline_tag in self.PIPELINE_CATEGORIES:
            categories.append(self.PIPELINE_CATEGORIES[pipeline_tag])
        
        # 从标签推断更多分类
        tags = model.get('tags', [])
        for tag in tags:
            tag_lower = tag.lower()
            if 'image' in tag_lower or 'vision' in tag_lower:
                categories.append('image')
            elif 'audio' in tag_lower or 'speech' in tag_lower:
                categories.append('voice')
            elif 'video' in tag_lower:
                categories.append('video')
            elif 'code' in tag_lower or 'programming' in tag_lower:
                categories.append('coding')
        
        categories = list(set(categories)) if categories else ['other']
        
        # 生成描述
        description = self._generate_model_description(model_id, pipeline_tag, tags, downloads)
        
        # 计算热度分数
        trending_score = min(100, int(likes / 100) + int(downloads / 100000))
        
        return self.create_product(
            name=name,
            description=description,
            logo_url="https://huggingface.co/front/assets/huggingface_logo-noborder.svg",
            website=f"{self.WEB_BASE}/{model_id}",
            categories=categories,
            rating=min(5.0, 4.0 + likes / 10000),
            weekly_users=downloads // 7,  # 估算周下载量
            trending_score=trending_score,
            source='huggingface',
            extra={
                'model_id': model_id,
                'downloads': downloads,
                'likes': likes,
                'pipeline_tag': pipeline_tag,
                'tags': tags[:10]  # 限制标签数量
            }
        )
    
    def _generate_model_description(self, model_id: str, pipeline: str, tags: List, downloads: int) -> str:
        """生成模型描述"""
        parts = []
        
        # 模型名称
        parts.append(f"Hugging Face 模型: {model_id}")
        
        # 任务类型
        pipeline_names = {
            'text-generation': '文本生成',
            'text-to-image': '文本转图像',
            'image-to-text': '图像描述',
            'automatic-speech-recognition': '语音识别',
            'text-to-speech': '文字转语音',
            'translation': '翻译',
            'summarization': '文本摘要',
            'conversational': '对话',
        }
        if pipeline in pipeline_names:
            parts.append(f"任务: {pipeline_names[pipeline]}")
        
        # 下载量
        if downloads > 1000000:
            parts.append(f"下载量: {downloads // 1000000}M+")
        elif downloads > 1000:
            parts.append(f"下载量: {downloads // 1000}K+")
        
        return ' | '.join(parts)
    
    def _get_trending_spaces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门 Spaces"""
        url = f"{self.API_BASE}/spaces"
        params = {
            'sort': 'trending',
            'limit': limit,
            'full': 'true'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            spaces_data = response.json()
        except Exception as e:
            # 备用：按点赞排序
            params['sort'] = 'likes'
            response = self.session.get(url, params=params, timeout=30)
            spaces_data = response.json()
        
        products = []
        
        for space in spaces_data:
            try:
                product = self._parse_space(space)
                if product:
                    products.append(product)
            except Exception as e:
                continue
        
        return products
    
    def _parse_space(self, space: Dict) -> Dict[str, Any]:
        """解析 Space 数据"""
        space_id = space.get('id', '')
        if not space_id:
            return None
        
        name = space_id.split('/')[-1] if '/' in space_id else space_id
        
        # 获取元数据
        likes = space.get('likes', 0)
        
        # 获取 SDK 类型
        sdk = space.get('sdk', 'gradio')
        
        # 推断分类
        tags = space.get('tags', [])
        categories = self._infer_space_categories(name, tags, sdk)
        
        # 生成描述
        description = f"Hugging Face Space: {space_id}"
        if sdk:
            description += f" (使用 {sdk})"
        
        # 计算热度
        trending_score = min(100, likes // 10 + 50)
        
        return self.create_product(
            name=name,
            description=description,
            logo_url="https://huggingface.co/front/assets/huggingface_logo-noborder.svg",
            website=f"{self.WEB_BASE}/spaces/{space_id}",
            categories=categories,
            rating=min(5.0, 4.0 + likes / 5000),
            weekly_users=likes * 100,  # 估算
            trending_score=trending_score,
            source='huggingface_spaces',
            extra={
                'space_id': space_id,
                'likes': likes,
                'sdk': sdk,
                'tags': tags[:10]
            }
        )
    
    def _infer_space_categories(self, name: str, tags: List, sdk: str) -> List[str]:
        """推断 Space 分类"""
        text = f"{name} {' '.join(tags)}".lower()
        categories = set()
        
        if any(kw in text for kw in ['image', 'vision', 'diffusion', 'stable', 'art', 'draw', 'paint']):
            categories.add('image')
        if any(kw in text for kw in ['video', 'animation']):
            categories.add('video')
        if any(kw in text for kw in ['audio', 'speech', 'voice', 'music', 'sound', 'tts']):
            categories.add('voice')
        if any(kw in text for kw in ['code', 'programming', 'developer']):
            categories.add('coding')
        if any(kw in text for kw in ['chat', 'llm', 'gpt', 'text', 'write']):
            categories.add('writing')
        
        return list(categories) if categories else ['other']


