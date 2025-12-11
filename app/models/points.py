from datetime import datetime
from ..extensions import db


class UserPointLog(db.Model):
    __tablename__ = 'user_point_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(20), default='general')  # sleep, shop, general 등
    sleep_log_id = db.Column(db.Integer, db.ForeignKey('sleep_logs.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
