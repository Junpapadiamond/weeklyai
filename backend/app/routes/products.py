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
        limit = request.args.get('limit', 15, type=int)
        products = ProductService.get_weekly_top_products(limit=limit)
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


@products_bp.route('/blogs', methods=['GET'])
def get_blogs_news():
    """获取博客/新闻/讨论内容"""
    try:
        limit = request.args.get('limit', 20, type=int)
        source = request.args.get('source', '')
        market = request.args.get('market', '')

        if source:
            blogs = ProductService.get_blogs_by_source(source, limit=limit, market=market)
        else:
            blogs = ProductService.get_blogs_news(limit=limit, market=market)

        return jsonify({
            'success': True,
            'data': blogs,
            'message': '获取博客/新闻成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500


@products_bp.route('/dark-horses', methods=['GET'])
def get_dark_horse_products():
    """获取本周黑马产品 - 高潜力新兴产品"""
    try:
        limit = request.args.get('limit', 10, type=int)
        min_index = request.args.get('min_index', 4, type=int)
        products = ProductService.get_dark_horse_products(limit=limit, min_index=min_index)
        return jsonify({
            'success': True,
            'data': products,
            'message': '获取黑马产品成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500


@products_bp.route('/rising-stars', methods=['GET'])
def get_rising_star_products():
    """获取潜力股产品 - 2-3分的有潜力产品"""
    try:
        limit = request.args.get('limit', 20, type=int)
        products = ProductService.get_rising_star_products(limit=limit)
        return jsonify({
            'success': True,
            'data': products,
            'message': '获取潜力股产品成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': str(e)
        }), 500


@products_bp.route('/today', methods=['GET'])
def get_todays_picks():
    """获取今日精选 - 最近48小时内的新产品宝藏

    Query参数:
    - limit: 返回数量，默认10
    - hours: 时间窗口（小时），默认48
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        hours = request.args.get('hours', 48, type=int)
        products = ProductService.get_todays_picks(limit=limit, hours=hours)
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products),
            'message': f'获取最近{hours}小时内的{len(products)}个新产品'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'count': 0,
            'message': str(e)
        }), 500


@products_bp.route('/last-updated', methods=['GET'])
def get_last_updated():
    """获取最近一次数据更新时间"""
    try:
        info = ProductService.get_last_updated()
        return jsonify({
            'success': True,
            'last_updated': info.get('last_updated'),
            'hours_ago': info.get('hours_ago'),
            'message': '获取数据更新时间成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'last_updated': None,
            'hours_ago': None,
            'message': str(e)
        }), 500


@products_bp.route('/<product_id>/related', methods=['GET'])
def get_related_products(product_id):
    """获取相关产品 - 基于分类和标签的相似产品推荐

    Query参数:
    - limit: 返回数量，默认6
    """
    try:
        limit = request.args.get('limit', 6, type=int)
        related = ProductService.get_related_products(product_id, limit=limit)
        return jsonify({
            'success': True,
            'data': related,
            'count': len(related),
            'message': f'获取{len(related)}个相关产品'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'count': 0,
            'message': str(e)
        }), 500


@products_bp.route('/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """获取数据分析摘要 - 分类分布、趋势方向、热门产品"""
    try:
        summary = ProductService.get_analytics_summary()
        return jsonify({
            'success': True,
            'data': summary,
            'message': '获取分析摘要成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': str(e)
        }), 500


@products_bp.route('/feed/rss', methods=['GET'])
def get_rss_feed():
    """获取RSS订阅源 - 最新产品的XML feed"""
    try:
        from flask import Response
        rss_xml = ProductService.generate_rss_feed()
        return Response(rss_xml, mimetype='application/rss+xml')
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@products_bp.route('/industry-leaders', methods=['GET'])
def get_industry_leaders():
    """获取行业领军产品 - 已知名的成熟 AI 产品参考列表"""
    try:
        data = ProductService.get_industry_leaders()
        return jsonify({
            'success': True,
            'data': data,
            'message': '获取行业领军产品成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': str(e)
        }), 500

