from flask import Blueprint, jsonify, request
from app.services.product_service import ProductService

products_bp = Blueprint('products', __name__)

@products_bp.route('/trending', methods=['GET'])
def get_trending_products():
    """获取热门推荐产品（前5个）"""
    try:
        products = ProductService.get_trending_products(limit=5)
        return jsonify({
            'success': True,
            'data': products,
            'message': '获取热门产品成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500

@products_bp.route('/weekly-top', methods=['GET'])
def get_weekly_top_products():
    """获取本周Top 15产品"""
    try:
        products = ProductService.get_weekly_top_products(limit=15)
        return jsonify({
            'success': True,
            'data': products,
            'message': '获取本周Top产品成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500

@products_bp.route('/<product_id>', methods=['GET'])
def get_product_detail(product_id):
    """获取产品详情"""
    try:
        product = ProductService.get_product_by_id(product_id)
        if product:
            return jsonify({
                'success': True,
                'data': product,
                'message': '获取产品详情成功'
            })
        return jsonify({
            'success': False,
            'data': None,
            'message': '产品不存在'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': str(e)
        }), 500

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    categories = [
        {'id': 'coding', 'name': '编程开发', 'icon': '💻'},
        {'id': 'voice', 'name': '语音识别', 'icon': '🎤'},
        {'id': 'finance', 'name': '金融科技', 'icon': '💰'},
        {'id': 'image', 'name': '图像处理', 'icon': '🖼️'},
        {'id': 'video', 'name': '视频生成', 'icon': '🎬'},
        {'id': 'writing', 'name': '写作助手', 'icon': '✍️'},
        {'id': 'healthcare', 'name': '医疗健康', 'icon': '🏥'},
        {'id': 'education', 'name': '教育学习', 'icon': '📚'},
        {'id': 'hardware', 'name': '硬件设备', 'icon': '🔧'},
        {'id': 'other', 'name': '其他', 'icon': '🔮'}
    ]
    return jsonify({
        'success': True,
        'data': categories,
        'message': '获取分类成功'
    })


