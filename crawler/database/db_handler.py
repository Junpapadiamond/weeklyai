"""
数据库处理模块
支持 MongoDB 和 MySQL 双数据库存储
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


class DatabaseHandler:
    """数据库处理类"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mysql_conn = None
        
        self._init_mongodb()
        self._init_mysql()
    
    def _init_mongodb(self):
        """初始化 MongoDB 连接"""
        if not HAS_MONGO:
            print("  ⚠ pymongo 未安装，跳过 MongoDB")
            return
        
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/weeklyai')
        
        try:
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            # 测试连接
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client.get_database()
            print("  ✓ MongoDB 连接成功")
        except Exception as e:
            print(f"  ⚠ MongoDB 连接失败: {e}")
            self.mongo_db = None
    
    def _init_mysql(self):
        """初始化 MySQL 连接"""
        if not HAS_MYSQL:
            print("  ⚠ mysql-connector-python 未安装，跳过 MySQL")
            return
        
        try:
            self.mysql_conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', 'localhost'),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'weeklyai'),
                charset='utf8mb4'
            )
            self._create_mysql_tables()
            print("  ✓ MySQL 连接成功")
        except Exception as e:
            print(f"  ⚠ MySQL 连接失败: {e}")
            self.mysql_conn = None
    
    def _create_mysql_tables(self):
        """创建 MySQL 表"""
        if not self.mysql_conn:
            return
        
        cursor = self.mysql_conn.cursor()
        
        # 采集日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                source VARCHAR(100) NOT NULL,
                products_count INT DEFAULT 0,
                status ENUM('success', 'failed', 'partial') DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        self.mysql_conn.commit()
        cursor.close()
    
    def save_products(self, products: List[Dict[str, Any]]) -> int:
        """
        保存产品到 MongoDB
        使用 upsert 避免重复
        """
        if self.mongo_db is None or not products:
            return 0
        
        collection = self.mongo_db.products
        saved_count = 0
        
        for product in products:
            try:
                # 复制并清理数据
                doc = {k: v for k, v in product.items() if v is not None}
                
                # 添加时间戳
                doc['updated_at'] = datetime.utcnow()
                
                # 处理 extra 字段（展开或序列化）
                if 'extra' in doc and isinstance(doc['extra'], dict):
                    doc['extra'] = json.dumps(doc['extra'], ensure_ascii=False)
                
                # 使用 name + source 作为唯一标识
                result = collection.update_one(
                    {
                        'name': doc['name'],
                        'source': doc.get('source', 'unknown')
                    },
                    {
                        '$set': doc,
                        '$setOnInsert': {'created_at': datetime.utcnow()}
                    },
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count:
                    saved_count += 1
                    
            except Exception as e:
                print(f"    保存失败 {product.get('name', 'unknown')}: {e}")
                continue
        
        # 记录采集日志
        source = products[0].get('source', 'mixed') if products else 'unknown'
        self._log_crawl(source, saved_count, 'success')
        
        return saved_count
    
    def get_trending_products(self, limit: int = 5) -> List[Dict]:
        """获取热门产品"""
        if self.mongo_db is None:
            return self._get_from_file('trending', limit)
        
        collection = self.mongo_db.products
        products = list(collection.find(
            {},
            {'_id': 0}
        ).sort('hot_score', -1).limit(limit))
        
        # 如果没有 hot_score，用 final_score 或 trending_score
        if not products:
            products = list(collection.find(
                {},
                {'_id': 0}
            ).sort('final_score', -1).limit(limit))
        if not products:
            products = list(collection.find(
                {},
                {'_id': 0}
            ).sort('trending_score', -1).limit(limit))
        
        return products
    
    def get_weekly_top(self, limit: int = 15) -> List[Dict]:
        """获取本周Top产品"""
        if self.mongo_db is None:
            return self._get_from_file('weekly', limit)
        
        collection = self.mongo_db.products
        products = list(collection.find(
            {},
            {'_id': 0}
        ).sort([('top_score', -1), ('final_score', -1), ('weekly_users', -1)]).limit(limit))
        
        return products
    
    def search_products(self, query: str = '', categories: List[str] = None,
                       limit: int = 20) -> List[Dict]:
        """搜索产品"""
        if self.mongo_db is None:
            return self._search_from_file(query, categories, limit)
        
        collection = self.mongo_db.products
        
        # 构建查询条件
        filter_query = {}
        
        if query:
            filter_query['$or'] = [
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}}
            ]
        
        if categories:
            filter_query['categories'] = {'$in': categories}
        
        products = list(collection.find(
            filter_query,
            {'_id': 0}
        ).sort('final_score', -1).limit(limit))
        
        return products
    
    def _get_from_file(self, query_type: str, limit: int) -> List[Dict]:
        """从本地文件获取数据"""
        data_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 'data', 'products_latest.json'
        )
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            # 排序
            if query_type == 'trending':
                products.sort(
                    key=lambda x: x.get('final_score', x.get('trending_score', 0)),
                    reverse=True
                )
            elif query_type == 'weekly':
                products.sort(
                    key=lambda x: x.get('weekly_users', 0),
                    reverse=True
                )
            
            return products[:limit]
        except:
            return []
    
    def _search_from_file(self, query: str, categories: List[str], limit: int) -> List[Dict]:
        """从文件搜索"""
        products = self._get_from_file('trending', 1000)
        
        results = []
        for p in products:
            # 关键词匹配
            if query:
                text = f"{p.get('name', '')} {p.get('description', '')}".lower()
                if query.lower() not in text:
                    continue
            
            # 分类匹配
            if categories:
                p_cats = p.get('categories', [])
                if not any(c in p_cats for c in categories):
                    continue
            
            results.append(p)
            if len(results) >= limit:
                break
        
        return results
    
    def _log_crawl(self, source: str, count: int, status: str,
                   error_message: str = None):
        """记录采集日志"""
        if not self.mysql_conn:
            return
        
        try:
            cursor = self.mysql_conn.cursor()
            cursor.execute("""
                INSERT INTO crawl_logs (source, products_count, status, error_message)
                VALUES (%s, %s, %s, %s)
            """, (source, count, status, error_message))
            self.mysql_conn.commit()
            cursor.close()
        except Exception as e:
            pass  # 日志失败不影响主流程
    
    def close(self):
        """关闭数据库连接"""
        if self.mongo_client:
            try:
                self.mongo_client.close()
            except:
                pass
        if self.mysql_conn:
            try:
                self.mysql_conn.close()
            except:
                pass
