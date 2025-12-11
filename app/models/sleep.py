from datetime import datetime
from ..extensions import db


class SleepLog(db.Model):
    __tablename__ = 'sleep_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    awarded_minutes = db.Column(db.Integer, default=0)  # 이미 포인트로 인정한 분 수
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
        db.Index('idx_sleep_logs_user_awarded', 'user_id', 'awarded_minutes'),
    )


class DailySleepPointBank(db.Model):
    __tablename__ = 'daily_sleep_point_banks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_key = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD (정오 기준)
    pending_points = db.Column(db.Numeric(10, 1), default=0.0)  # 타이머 포인트 (광고 보기 전)
    claimed_points = db.Column(db.Numeric(10, 1), default=0.0)  # 타이머 포인트 (광고 보고 받은)
    intermediate_claimed_count = db.Column(db.Integer, default=0)  # 중간 획득 횟수 (최대 5회)
    intermediate_claimed_points = db.Column(db.Numeric(10, 1), default=0.0)  # 중간 획득 포인트 총합
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date_key'),
        db.Index('idx_daily_sleep_point_banks_user_date', 'user_id', 'date_key'),
    )


class SleepIntermediateClaim(db.Model):
    __tablename__ = 'sleep_intermediate_claims'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sleep_log_id = db.Column(db.Integer, db.ForeignKey('sleep_logs.id'), nullable=False)
    claim_sequence = db.Column(db.Integer, nullable=False)  # 1~5번째 획득
    points_awarded = db.Column(db.Numeric(10, 1), default=10.0)
    claimed_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('sleep_log_id', 'claim_sequence'),
        db.Index('idx_sleep_intermediate_claims_user', 'user_id'),
        db.Index('idx_sleep_intermediate_claims_session', 'sleep_log_id'),
    )
