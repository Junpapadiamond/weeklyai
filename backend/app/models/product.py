from datetime import datetime
from bson import ObjectId

class Product:
    """AI产品模型"""
    
    CATEGORIES = [
        'coding',      # 编程相关
        'voice',       # 语音相关
        'finance',     # 金融相关
        'image',       # 图像相关
        'video',       # 视频相关
        'writing',     # 写作相关
        'healthcare',  # 医疗相关
        'education',   # 教育相关
        'hardware',    # 硬件设备
        'other'        # 其他
    ]
    
    def __init__(self, name, description, logo_url, website, categories, 
                 rating=0, weekly_users=0, trending_score=0):
        self.name = name
        self.description = description
        self.logo_url = logo_url
        self.website = website
        self.categories = categories  # 列表，支持多分类
        self.rating = rating
        self.weekly_users = weekly_users
        self.trending_score = trending_score
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'logo_url': self.logo_url,
            'website': self.website,
            'categories': self.categories,
            'rating': self.rating,
            'weekly_users': self.weekly_users,
            'trending_score': self.trending_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建产品"""
        product = Product(
            name=data.get('name'),
            description=data.get('description'),
            logo_url=data.get('logo_url'),
            website=data.get('website'),
            categories=data.get('categories', []),
            rating=data.get('rating', 0),
            weekly_users=data.get('weekly_users', 0),
            trending_score=data.get('trending_score', 0)
        )
        if 'created_at' in data:
            product.created_at = data['created_at']
        if 'updated_at' in data:
            product.updated_at = data['updated_at']
        return product


