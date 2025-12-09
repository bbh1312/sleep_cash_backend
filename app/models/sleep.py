from datetime import datetime
from ..extensions import db


class SleepLog(db.Model):
    __tablename__ = 'sleep_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    total_sleep_minutes = db.Column(db.Integer)
    sleep_score = db.Column(db.Integer)
