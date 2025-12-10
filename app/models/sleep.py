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
    mood = db.Column(db.String(20))
    memo = db.Column(db.Text)
    white_noise_type = db.Column(db.String(50))
    white_noise_volume = db.Column(db.Integer)
    status = db.Column(db.String(20), default='running', nullable=False)  # running, ended
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('idx_sleep_logs_user_status', 'user_id', 'status'),
    )
