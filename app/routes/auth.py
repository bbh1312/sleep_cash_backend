from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from ..extensions import db
from ..models.user import User
from ..services.social_auth import SocialAuthError, verify_social_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/social-login')
def social_login():
    data = request.get_json() or {}
    provider = data.get('provider')
    token = data.get('token')
    if not provider or not token:
        return {'message': 'provider와 token은 필수입니다.'}, 400

    try:
        profile = verify_social_token(provider, token)
    except SocialAuthError as exc:
        status = 503 if exc.code == 'provider_unavailable' else 401
        return {'message': exc.message, 'code': exc.code}, status

    if not profile.get('provider_user_id'):
        return {'message': '제공자로부터 사용자 정보를 가져오지 못했습니다.'}, 502

    user = User.query.filter_by(
        provider=profile['provider'],
        provider_user_id=profile['provider_user_id']
    ).first()

    is_new_user = False
    if not user:
        user = User(
            provider=profile['provider'],
            provider_user_id=profile['provider_user_id'],
            email=profile.get('email'),
            display_name=profile.get('display_name'),
            profile_image_url=profile.get('profile_image_url'),
        )
        db.session.add(user)
        is_new_user = True
    else:
        if profile.get('email'):
            user.email = profile['email']
        if profile.get('display_name'):
            user.display_name = profile['display_name']
        if profile.get('profile_image_url'):
            user.profile_image_url = profile['profile_image_url']

    user.last_login_at = datetime.utcnow()
    db.session.commit()
    access_token = create_access_token(identity=user.id)

    return {'access_token': access_token, 'is_new_user': is_new_user}
