from datetime import datetime
from ..extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    profile_image_url = db.Column(db.String(500))
    total_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_user_provider_identity'),
    )
