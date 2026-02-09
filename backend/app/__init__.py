from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import Config
from functools import wraps
from collections import defaultdict
import time

mongo = PyMongo()

# Simple in-memory rate limiter
class RateLimiter:
    """Simple in-memory rate limiter (100 requests per minute per IP)"""
    def __init__(self, requests_per_minute=100):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, key):
        now = time.time()
        minute_ago = now - 60

        # Clean old entries
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]

        # Check if allowed
        if len(self.requests[key]) >= self.requests_per_minute:
            return False

        # Record this request
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=100)

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS: use explicit allowlist in production when provided.
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    else:
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 初始化 MongoDB
    mongo.init_app(app)

    # Rate limiting middleware
    @app.before_request
    def check_rate_limit():
        if request.path.startswith('/api/'):
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            if not rate_limiter.is_allowed(client_ip):
                return jsonify({
                    'success': False,
                    'message': 'Rate limit exceeded. Please wait a moment.',
                    'error': 'TOO_MANY_REQUESTS'
                }), 429

    # 注册蓝图
    from app.routes.products import products_bp
    from app.routes.search import search_bp

    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')

    return app


