import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'weeklyai-secret-key-2024')
    
    # MongoDB 配置
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
    
    # MySQL 配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'weeklyai')
    
    # API 配置
    API_PREFIX = '/api/v1'


