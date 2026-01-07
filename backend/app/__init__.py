from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import Config

mongo = PyMongo()

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 启用 CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化 MongoDB
    mongo.init_app(app)
    
    # 注册蓝图
    from app.routes.products import products_bp
    from app.routes.search import search_bp
    
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')
    
    return app


