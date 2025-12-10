from datetime import datetime
from ..extensions import db


class ShopProduct(db.Model):
    __tablename__ = 'shop_products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255))
    detail_description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    tag = db.Column(db.String(50))
    price = db.Column(db.Integer, nullable=False)
    discount_rate = db.Column(db.Integer)
    rating = db.Column(db.Float)
    review_count = db.Column(db.Integer)
    is_recommended = db.Column(db.Boolean, default=False, nullable=False)
    thumb_url = db.Column(db.String(500))
    icon_bg_color = db.Column(db.String(20))
    source = db.Column(db.String(50), default='coupang', nullable=False)
    partners_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.Index('idx_shop_products_category', 'category'),
        db.Index('idx_shop_products_is_recommended', 'is_recommended'),
        db.Index('idx_shop_products_is_active', 'is_active'),
    )


class ShopClickLog(db.Model):
    __tablename__ = 'shop_click_logs'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('shop_products.id'), nullable=False)
    source = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    out_url = db.Column(db.Text)

    product = db.relationship('ShopProduct', backref=db.backref('click_logs', lazy='dynamic'))
