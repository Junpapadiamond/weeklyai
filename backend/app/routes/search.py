from flask import Blueprint, jsonify, request
from app.services.product_service import ProductService

search_bp = Blueprint('search', __name__)


def _parse_positive_int(raw_value, default: int, minimum: int, maximum: int) -> int:
    """Parse int query params with guard rails."""
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


@search_bp.route('/', methods=['GET'])
def search_products():
    """
    搜索产品
    
    Query Parameters:
    - q: 搜索关键词
    - categories: 分类筛选（逗号分隔，支持多选）
    - type: 类型筛选 (software/hardware/all)
    - sort: 排序方式 (trending/rating/users)
    - page: 页码
    - limit: 每页数量
    """
    try:
        # 获取查询参数
        keyword = request.args.get('q', '').strip()
        categories = request.args.get('categories', '')
        product_type = request.args.get('type', 'all').strip().lower()
        sort_by = request.args.get('sort', 'trending').strip().lower()
        page = _parse_positive_int(request.args.get('page', 1), default=1, minimum=1, maximum=10_000)
        limit = _parse_positive_int(request.args.get('limit', 15), default=15, minimum=1, maximum=50)

        # 解析分类
        category_list = [c.strip() for c in categories.split(',') if c.strip()]
        
        # 执行搜索
        results = ProductService.search_products(
            keyword=keyword,
            categories=category_list,
            product_type=product_type,
            sort_by=sort_by,
            page=page,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': results['products'],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': results['total'],
                'pages': (results['total'] + limit - 1) // limit
            },
            'message': '搜索成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500


