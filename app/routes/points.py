from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import User
from ..models.points import UserPointLog
points_bp = Blueprint('points','points')

@points_bp.get('/balance')
@jwt_required()
def bal(): return {'total_points': User.query.get(get_jwt_identity()).total_points}

@points_bp.get('/history')
@jwt_required()
def hist():
    uid=get_jwt_identity()
    rows=UserPointLog.query.filter_by(user_id=uid).all()
    return [{'id':r.id,'change':r.change,'bal':r.balance_after} for r in rows]
