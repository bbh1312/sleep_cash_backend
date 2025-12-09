import requests
from flask import current_app
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class SocialAuthError(Exception):
    """소셜 로그인 검증 시 발생하는 예외."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def verify_social_token(provider: str, token: str) -> dict:
    provider = (provider or '').lower()
    if provider == 'google':
        return _verify_google_token(token)
    if provider == 'kakao':
        return _verify_kakao_token(token)
    raise SocialAuthError('unsupported_provider', '지원하지 않는 로그인 제공자입니다.')


def _verify_google_token(token: str) -> dict:
    if not token:
        raise SocialAuthError('invalid_token', '구글 토큰이 전달되지 않았습니다.')
    request = google_requests.Request()
    audience = current_app.config.get('GOOGLE_CLIENT_ID')
    try:
        payload = id_token.verify_oauth2_token(token, request, audience=audience)
    except ValueError as exc:  # 검증 실패
        raise SocialAuthError('invalid_token', '구글 토큰 검증에 실패했습니다.') from exc

    return {
        'provider': 'google',
        'provider_user_id': payload.get('sub'),
        'email': payload.get('email'),
        'display_name': payload.get('name'),
        'profile_image_url': payload.get('picture'),
    }


def _verify_kakao_token(token: str) -> dict:
    if not token:
        raise SocialAuthError('invalid_token', '카카오 토큰이 전달되지 않았습니다.')
    headers = {'Authorization': f'Bearer {token}'}
    try:
        resp = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers, timeout=5)
    except requests.RequestException as exc:
        raise SocialAuthError('provider_unavailable', '카카오 인증 서버에 연결할 수 없습니다.') from exc

    if resp.status_code != 200:
        raise SocialAuthError('invalid_token', '카카오 토큰 검증에 실패했습니다.')

    data = resp.json()
    kakao_account = data.get('kakao_account') or {}
    profile = kakao_account.get('profile') or {}

    return {
        'provider': 'kakao',
        'provider_user_id': str(data.get('id')),
        'email': kakao_account.get('email'),
        'display_name': profile.get('nickname'),
        'profile_image_url': profile.get('profile_image_url') or profile.get('thumbnail_image_url'),
    }
