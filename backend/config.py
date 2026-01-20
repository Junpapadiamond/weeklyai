import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    """应用配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'weeklyai-secret-key-2024')
    
    # 数据路径 (Docker 部署时使用 /data，本地开发时使用 crawler/data)
    DATA_PATH = os.getenv('DATA_PATH', str(PROJECT_ROOT / 'crawler' / 'data'))
    
    # MongoDB 配置
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
    
    # MySQL 配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'weeklyai')
    
    # API 配置
    API_PREFIX = '/api/v1'
    
    # Flask 环境
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')


