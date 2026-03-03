import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    """应用配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'weeklyai-secret-key-2024')
    
    # 数据路径:
    # 1) 优先使用环境变量 DATA_PATH
    # 2) 本地开发默认使用 crawler/data
    # 3) 若不存在则回退到 backend/data（适配 Vercel backend 独立部署）
    _default_crawler_data = PROJECT_ROOT / 'crawler' / 'data'
    _default_backend_data = Path(__file__).parent / 'data'
    DATA_PATH = os.getenv(
        'DATA_PATH',
        str(_default_crawler_data if _default_crawler_data.exists() else _default_backend_data)
    )
    
    # MongoDB 配置
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
    
    # MySQL 配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'weeklyai')
    
    # API 配置
    API_PREFIX = '/api/v1'

    # CORS allowlist (comma-separated origins)
    # Example:
    # CORS_ALLOWED_ORIGINS=https://weeklyai.vercel.app,https://www.weeklyai.com
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        if origin.strip()
    ]
    
    # Flask 环境
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Dark Horse rotation settings (days)
    # FRESH_DAYS: Most products leave Weekly Black Horse after this many days
    # STICKY_DAYS: Top 1 product (highest score+funding) can stay this long
    DARK_HORSE_FRESH_DAYS = int(os.getenv('DARK_HORSE_FRESH_DAYS', '5'))
    DARK_HORSE_STICKY_DAYS = int(os.getenv('DARK_HORSE_STICKY_DAYS', '10'))
