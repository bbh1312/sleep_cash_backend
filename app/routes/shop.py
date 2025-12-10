from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models.shop import ShopProduct, ShopClickLog

shop_bp = Blueprint('shop', __name__)


def _serialize_list_item(product: ShopProduct):
    return {
        'id': product.id,
        'title': product.title,
        'subtitle': product.subtitle,
        'category': product.category,
        'tag': product.tag,
        'price': product.price,
        'discount_rate': product.discount_rate,
        'rating': product.rating,
        'review_count': product.review_count,
        'is_recommended': product.is_recommended,
        'thumb_url': product.thumb_url,
        'icon_bg_color': product.icon_bg_color,
    }


def _serialize_detail(product: ShopProduct):
    data = _serialize_list_item(product)
    data.update({
        'detail_description': product.detail_description or product.subtitle,
        'source': product.source,
    })
    return data


@shop_bp.get('/products')
def list_products():
    category = request.args.get('category', 'all')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.args.get('page_size', 20))
    except ValueError:
        page_size = 20

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    query = ShopProduct.query.filter_by(is_active=True)
    if category and category != 'all':
        query = query.filter(ShopProduct.category == category)

    total = query.count()
    items = (
        query
        .order_by(ShopProduct.is_recommended.desc(), ShopProduct.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        'items': [_serialize_list_item(p) for p in items],
        'page': page,
        'page_size': page_size,
        'total': total,
    }


@shop_bp.get('/products/<int:product_id>')
def get_product(product_id):
    product = ShopProduct.query.get(product_id)
    if not product:
        return {'message': '상품을 찾을 수 없습니다.'}, 404
    if not product.is_active:
        return {'message': '비활성화된 상품입니다.'}, 410

    return _serialize_detail(product)


@shop_bp.post('/products/<int:product_id>/click')
def click_product(product_id):
    product = ShopProduct.query.get(product_id)
    if not product:
        return {'message': '상품을 찾을 수 없습니다.'}, 404
    if not product.is_active:
        return {'message': '비활성화된 상품입니다.'}, 410

    # JWT가 있으면 사용, 없어도 통과
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        user_id = None

    payload = request.get_json(silent=True) or {}
    source = payload.get('source')
    user_agent = request.headers.get('User-Agent')

    log = ShopClickLog(
        user_id=user_id,
        product_id=product.id,
        source=source,
        user_agent=user_agent,
        out_url=product.partners_url,
    )
    db.session.add(log)
    db.session.commit()

    return {'redirect_url': product.partners_url}
