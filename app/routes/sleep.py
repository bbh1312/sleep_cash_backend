from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..extensions import db
from ..models.sleep import SleepLog
from ..models.user import User
from ..models.points import UserPointLog
sleep_bp = Blueprint('sleep', __name__)

@sleep_bp.post('/sessions')
@jwt_required()
def start():
    sid = get_jwt_identity()
    log = SleepLog(user_id=sid, started_at=datetime.utcnow())
    db.session.add(log); db.session.commit(); return {'session_id': log.id}, 201

@sleep_bp.patch('/sessions/<int:id>/end')
@jwt_required()
def end(id):
    uid = get_jwt_identity()
    log = SleepLog.query.filter_by(id=id, user_id=uid).first()
    if not log: return {'message':'notfound'},404
    log.ended_at = datetime.utcnow()
    mins = int((log.ended_at - log.started_at).total_seconds()//60)
    log.total_sleep_minutes, log.sleep_score = mins, 80
    u = User.query.get(uid); reward=50; u.total_points+=reward
    txn = UserPointLog(
        user_id=uid,
        change=reward,
        balance_after=u.total_points,
        type='sleep_reward',
        sleep_log_id=log.id,
    )
    db.session.add(txn); db.session.commit(); return {'session_id': log.id, 'reward_points': reward}
