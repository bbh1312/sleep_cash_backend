from flask import Blueprint
rewards_bp = Blueprint('rewards','rewards')
@rewards_bp.get('/')
def list(): return []
