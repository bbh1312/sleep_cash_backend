from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.sleep import SleepLog
from ..models.user import User
from ..models.points import UserPointLog

sleep_bp = Blueprint('sleep', __name__)

DAILY_SLEEP_POINT_LIMIT = 200


def _sleep_dict(session: SleepLog):
    return {
        'id': session.id,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        'total_sleep_minutes': session.total_sleep_minutes,
        'sleep_score': session.sleep_score,
        'mood': session.mood,
        'memo': session.memo,
        'white_noise_type': session.white_noise_type,
        'white_noise_volume': session.white_noise_volume,
        'status': session.status,
    }


def _today_sleep_points(user_id: int) -> int:
    """오늘 UTC 기준 수면 리워드 합계."""
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    total = (
        db.session.query(db.func.coalesce(db.func.sum(UserPointLog.change), 0))
        .filter(
            UserPointLog.user_id == user_id,
            UserPointLog.type == 'sleep_reward',
            UserPointLog.created_at >= start,
            UserPointLog.created_at < end,
        )
        .scalar()
    )
    return int(total or 0)


@sleep_bp.get('/active-session')
@jwt_required()
def active_session():
    uid = get_jwt_identity()
    session = (
        SleepLog.query
        .filter_by(user_id=uid, status='running', ended_at=None)
        .order_by(SleepLog.started_at.desc())
        .first()
    )
    if not session:
        return {'has_active_session': False}
    return {'has_active_session': True, 'session': _sleep_dict(session)}


@sleep_bp.post('/sessions')
@jwt_required()
def create_session():
    uid = get_jwt_identity()
    existing = SleepLog.query.filter_by(user_id=uid, status='running', ended_at=None).first()
    if existing:
        return {'message': '이미 진행 중인 세션이 있습니다.', 'session_id': existing.id}, 400

    data = request.get_json() or {}
    mood = data.get('mood')
    memo = data.get('memo')
    white_noise_type = data.get('white_noise_type')
    white_noise_volume = data.get('white_noise_volume')
    if white_noise_volume is not None:
        try:
            white_noise_volume = int(white_noise_volume)
        except ValueError:
            return {'message': 'white_noise_volume은 0~100 정수여야 합니다.'}, 400
        if white_noise_volume < 0 or white_noise_volume > 100:
            return {'message': 'white_noise_volume은 0~100 범위여야 합니다.'}, 400

    now = datetime.utcnow()
    session = SleepLog(
        user_id=uid,
        started_at=now,
        created_at=now,
        mood=mood,
        memo=memo,
        white_noise_type=white_noise_type,
        white_noise_volume=white_noise_volume,
        status='running',
    )
    db.session.add(session)
    db.session.commit()
    return {'session_id': session.id, 'started_at': session.started_at.isoformat()}, 201


@sleep_bp.get('/sessions/<int:session_id>')
@jwt_required()
def get_session(session_id):
    uid = get_jwt_identity()
    session = SleepLog.query.filter_by(id=session_id, user_id=uid).first()
    if not session:
        return {'message': '세션을 찾을 수 없습니다.'}, 404
    return _sleep_dict(session)


@sleep_bp.patch('/sessions/<int:session_id>')
@jwt_required()
def update_session(session_id):
    uid = get_jwt_identity()
    session = SleepLog.query.filter_by(id=session_id, user_id=uid).first()
    if not session:
        return {'message': '세션을 찾을 수 없습니다.'}, 404
    if session.status != 'running':
        return {'message': '종료된 세션은 수정할 수 없습니다.'}, 400

    data = request.get_json() or {}
    if 'mood' in data:
        session.mood = data.get('mood')
    if 'memo' in data:
        session.memo = data.get('memo')
    if 'white_noise_type' in data:
        session.white_noise_type = data.get('white_noise_type')
    if 'white_noise_volume' in data:
        try:
            volume = int(data.get('white_noise_volume'))
        except (TypeError, ValueError):
            return {'message': 'white_noise_volume은 0~100 정수여야 합니다.'}, 400
        if volume < 0 or volume > 100:
            return {'message': 'white_noise_volume은 0~100 범위여야 합니다.'}, 400
        session.white_noise_volume = volume

    db.session.commit()
    return _sleep_dict(session)


@sleep_bp.post('/sessions/<int:session_id>/end')
@jwt_required()
def end_session(session_id):
    uid = get_jwt_identity()
    session = SleepLog.query.filter_by(id=session_id, user_id=uid).first()
    if not session:
        return {'message': '세션을 찾을 수 없습니다.'}, 404
    if session.status != 'running' or session.ended_at is not None:
        return {'message': '이미 종료된 세션입니다.'}, 400

    now = datetime.utcnow()
    session.ended_at = now
    session.status = 'ended'
    session.total_sleep_minutes = max(int((now - session.started_at).total_seconds() // 60), 0)
    session.sleep_score = session.sleep_score or min(100, 70 + session.total_sleep_minutes // 10)

    today_points = _today_sleep_points(uid)
    remaining = max(DAILY_SLEEP_POINT_LIMIT - today_points, 0)
    points_earned = min(session.total_sleep_minutes or 0, remaining)

    user = User.query.get(uid)
    if user.total_points is None:
        user.total_points = 0
    user.total_points += points_earned

    txn = UserPointLog(
        user_id=uid,
        change=points_earned,
        balance_after=user.total_points,
        type='sleep_reward',
        sleep_log_id=session.id,
    )
    db.session.add(txn)
    db.session.commit()

    return {
        'session_id': session.id,
        'total_sleep_minutes': session.total_sleep_minutes,
        'sleep_score': session.sleep_score,
        'points_earned': points_earned,
        'today_total_points': today_points + points_earned,
        'daily_limit': DAILY_SLEEP_POINT_LIMIT,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'ended_at': session.ended_at.isoformat() if session.ended_at else None,
    }


@sleep_bp.post('/ad-impression')
@jwt_required(optional=True)
def ad_impression():
    # MVP: 로그 저장소가 없으므로 요청 데이터와 UA만 반환. 추후 DB/analytics로 확장.
    payload = request.get_json(silent=True) or {}
    return {'logged': True, 'event': 'impression', 'data': payload}, 200


@sleep_bp.post('/ad-click')
@jwt_required(optional=True)
def ad_click():
    payload = request.get_json(silent=True) or {}
    return {'logged': True, 'event': 'click', 'data': payload}, 200
