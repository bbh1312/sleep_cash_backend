from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models.sleep import SleepLog, DailySleepPointBank, SleepIntermediateClaim
from ..models.user import User
from ..models.points import UserPointLog

sleep_bp = Blueprint('sleep', __name__)

def get_noon_based_date(dt=None):
    """정오 기준 날짜 계산 (12:00 이후면 오늘, 이전이면 어제)"""
    if dt is None:
        dt = datetime.utcnow()
    
    noon_today = dt.replace(hour=12, minute=0, second=0, microsecond=0)
    if dt >= noon_today:
        return dt.date().strftime('%Y-%m-%d')
    else:
        yesterday = dt.date() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')

def get_or_create_daily_bank(user_id, date_key):
    """일일 포인트 뱅크 조회 또는 생성"""
    bank = DailySleepPointBank.query.filter_by(user_id=user_id, date_key=date_key).first()
    if not bank:
        bank = DailySleepPointBank(user_id=user_id, date_key=date_key)
        db.session.add(bank)
        db.session.flush()
    return bank

@sleep_bp.route('/start', methods=['POST'])
@jwt_required()
def start_sleep():
    user_id = get_jwt_identity()
    
    # 기존 활성 세션 확인
    existing = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    if existing:
        return jsonify({
            'success': False,
            'error': {'code': 'ACTIVE_SESSION_EXISTS', 'message': '이미 진행 중인 수면 세션이 있습니다.'}
        }), 400
    
    data = request.get_json() or {}
    
    # 새 세션 생성
    session = SleepLog(
        user_id=user_id,
        mood=data.get('mood'),
        memo=data.get('memo'),
        white_noise_type=data.get('white_noise_type'),
        white_noise_volume=data.get('white_noise_volume'),
        status='running'
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'session_id': session.id,
            'started_at': session.started_at.isoformat(),
            'status': session.status
        }
    })

@sleep_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    user_id = get_jwt_identity()
    now = datetime.utcnow()
    date_key = get_noon_based_date(now)
    
    # 현재 세션 조회
    session = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    if not session:
        return jsonify({
            'success': False,
            'error': {'code': 'NO_ACTIVE_SESSION', 'message': '활성화된 수면 세션이 없습니다.'}
        }), 404
    
    # 일일 뱅크 조회/생성
    bank = get_or_create_daily_bank(user_id, date_key)
    
    # 경과 시간 계산
    elapsed_minutes = int((now - session.started_at).total_seconds() // 60)
    
    return jsonify({
        'success': True,
        'data': {
            'session_id': session.id,
            'started_at': session.started_at.isoformat(),
            'elapsed_minutes': elapsed_minutes,
            'timer_points': {
                'claimed_points': float(bank.claimed_points),
                'daily_limit': 200,
                'remaining_limit': max(0, 200 - float(bank.claimed_points) - float(bank.intermediate_claimed_points))
            },
            'intermediate_points': {
                'claimed_count': bank.intermediate_claimed_count,
                'claimed_points': float(bank.intermediate_claimed_points),
                'max_claims': 5,
                'remaining_claims': max(0, 5 - bank.intermediate_claimed_count),
                'points_per_claim': 10
            },
            'status': session.status,
            'mood': session.mood,
            'white_noise_type': session.white_noise_type,
            'white_noise_volume': session.white_noise_volume
        }
    })

@sleep_bp.route('/claim-intermediate', methods=['POST'])
@jwt_required()
def claim_intermediate():
    user_id = get_jwt_identity()
    now = datetime.utcnow()
    date_key = get_noon_based_date(now)
    
    data = request.get_json() or {}
    accumulated_points = float(data.get('accumulated_points', 0))  # 프론트에서 계산한 적립 포인트
    
    # 현재 세션 확인
    session = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    if not session:
        return jsonify({
            'success': False,
            'error': {'code': 'NO_ACTIVE_SESSION', 'message': '활성화된 수면 세션이 없습니다.'}
        }), 404
    
    # 일일 뱅크 조회
    bank = get_or_create_daily_bank(user_id, date_key)
    
    # 중간 획득 한도 확인
    if bank.intermediate_claimed_count >= 5:
        return jsonify({
            'success': False,
            'error': {'code': 'INTERMEDIATE_LIMIT_REACHED', 'message': '오늘 중간 포인트 획득 한도에 도달했습니다.'}
        }), 400
    
    # 일일 한도 확인 (적립 포인트 + 10P)
    total_points_to_add = accumulated_points + 10.0
    current_total = float(bank.claimed_points) + float(bank.intermediate_claimed_points)
    if current_total + total_points_to_add > 200:
        available_points = max(0, 200 - current_total)
        return jsonify({
            'success': False,
            'error': {
                'code': 'DAILY_LIMIT_EXCEEDED', 
                'message': f'일일 한도를 초과합니다. 획득 가능: {available_points}P'
            }
        }), 400
    
    # 중간 포인트 획득 (적립 포인트 + 10P)
    claim_sequence = bank.intermediate_claimed_count + 1
    
    # 중간 획득 로그 생성
    claim = SleepIntermediateClaim(
        user_id=user_id,
        sleep_log_id=session.id,
        claim_sequence=claim_sequence,
        points_awarded=total_points_to_add
    )
    db.session.add(claim)
    
    # 뱅크 업데이트
    bank.intermediate_claimed_count += 1
    bank.intermediate_claimed_points = float(bank.intermediate_claimed_points) + total_points_to_add
    
    # 사용자 총 포인트 업데이트
    user = User.query.get(user_id)
    user.total_points = (user.total_points or 0) + int(total_points_to_add)
    
    # 포인트 로그 생성
    point_log = UserPointLog(
        user_id=user_id,
        change=int(total_points_to_add),
        balance_after=user.total_points,
        type='sleep_intermediate',
        source='sleep',
        sleep_log_id=session.id
    )
    db.session.add(point_log)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'claim_sequence': claim_sequence,
            'accumulated_points': accumulated_points,
            'bonus_points': 10.0,
            'total_points_awarded': total_points_to_add,
            'new_total_points': user.total_points,
            'remaining_claims': max(0, 5 - bank.intermediate_claimed_count),
            'total_intermediate_points': float(bank.intermediate_claimed_points)
        }
    })

@sleep_bp.route('/end', methods=['POST'])
@jwt_required()
def end_sleep():
    user_id = get_jwt_identity()
    now = datetime.utcnow()
    
    # 현재 세션 확인
    session = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    if not session:
        return jsonify({
            'success': False,
            'error': {'code': 'NO_ACTIVE_SESSION', 'message': '활성화된 수면 세션이 없습니다.'}
        }), 404
    
    # 세션 종료
    session.ended_at = now
    session.status = 'ended'
    session.total_sleep_minutes = int((now - session.started_at).total_seconds() // 60)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'session_id': session.id,
            'total_minutes': session.total_sleep_minutes,
            'ended_at': session.ended_at.isoformat()
        }
    })

@sleep_bp.route('/claim-timer', methods=['POST'])
@jwt_required()
def claim_timer():
    user_id = get_jwt_identity()
    date_key = get_noon_based_date()
    
    data = request.get_json() or {}
    accumulated_points = float(data.get('accumulated_points', 0))  # 프론트에서 계산한 적립 포인트
    ad_bonus = 10.0  # 광고 보너스
    
    if accumulated_points <= 0:
        return jsonify({
            'success': False,
            'error': {'code': 'NO_POINTS_TO_CLAIM', 'message': '획득할 포인트가 없습니다.'}
        }), 400
    
    # 일일 뱅크 조회
    bank = get_or_create_daily_bank(user_id, date_key)
    
    # 일일 한도 확인
    total_points_to_add = accumulated_points + ad_bonus
    current_total = float(bank.claimed_points) + float(bank.intermediate_claimed_points)
    if current_total + total_points_to_add > 200:
        available_points = max(0, 200 - current_total)
        return jsonify({
            'success': False,
            'error': {
                'code': 'DAILY_LIMIT_EXCEEDED',
                'message': f'일일 한도를 초과합니다. 획득 가능: {available_points}P'
            }
        }), 400
    
    # 포인트 지급
    user = User.query.get(user_id)
    user.total_points = (user.total_points or 0) + int(total_points_to_add)
    
    # 뱅크 업데이트
    bank.claimed_points = float(bank.claimed_points) + total_points_to_add
    
    # 포인트 로그 생성
    point_log = UserPointLog(
        user_id=user_id,
        change=int(total_points_to_add),
        balance_after=user.total_points,
        type='sleep_timer_claim',
        source='sleep'
    )
    db.session.add(point_log)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'accumulated_points': accumulated_points,
            'ad_bonus_points': ad_bonus,
            'total_claimed_points': total_points_to_add,
            'new_total_points': user.total_points,
            'type': 'timer_points'
        }
    })

@sleep_bp.route('/daily-status', methods=['GET'])
@jwt_required()
def daily_status():
    user_id = get_jwt_identity()
    date_key = get_noon_based_date()
    
    # 일일 뱅크 조회
    bank = get_or_create_daily_bank(user_id, date_key)
    
    # 현재 세션 확인
    current_session = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    session_data = None
    if current_session:
        elapsed_minutes = int((datetime.utcnow() - current_session.started_at).total_seconds() // 60)
        session_data = {
            'session_id': current_session.id,
            'status': current_session.status,
            'elapsed_minutes': elapsed_minutes
        }
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'date_key': date_key,
            'timer_points': {
                'claimed_points': float(bank.claimed_points),
                'daily_limit': 200,
                'remaining_limit': max(0, 200 - float(bank.claimed_points) - float(bank.intermediate_claimed_points))
            },
            'intermediate_points': {
                'claimed_count': bank.intermediate_claimed_count,
                'claimed_points': float(bank.intermediate_claimed_points),
                'max_claims': 5,
                'remaining_claims': max(0, 5 - bank.intermediate_claimed_count)
            },
            'total_today_points': float(bank.claimed_points) + float(bank.intermediate_claimed_points),
            'sleep_flow_completed': True,  # 프론트에서 로컬스토리지로 관리
            'current_session': session_data
        }
    })

@sleep_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_sleep():
    user_id = get_jwt_identity()
    
    # 현재 세션 확인
    session = SleepLog.query.filter_by(user_id=user_id, status='running').first()
    if not session:
        return jsonify({
            'success': False,
            'error': {'code': 'NO_ACTIVE_SESSION', 'message': '활성화된 수면 세션이 없습니다.'}
        }), 404
    
    data = request.get_json() or {}
    updated_fields = []
    
    if 'mood' in data:
        session.mood = data['mood']
        updated_fields.append('mood')
    
    if 'memo' in data:
        session.memo = data['memo']
        updated_fields.append('memo')
    
    if 'white_noise_type' in data:
        session.white_noise_type = data['white_noise_type']
        updated_fields.append('white_noise_type')
    
    if 'white_noise_volume' in data:
        session.white_noise_volume = data['white_noise_volume']
        updated_fields.append('white_noise_volume')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'session_id': session.id,
            'updated_fields': updated_fields
        }
    })
