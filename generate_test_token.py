#!/usr/bin/env python3
"""
테스트 유저용 JWT 토큰 발급 스크립트
"""
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def generate_test_token():
    # JWT 시크릿 키 (Flask-JWT-Extended 설정과 동일하게)
    secret_key = os.getenv('JWT_SECRET_KEY', 'change2')
    
    # 토큰 페이로드
    payload = {
        'sub': 1,  # Flask-JWT-Extended는 'sub' 사용
        'username': 'testuser',
        'email': 'test@sleepcash.com',
        'iat': datetime.utcnow(),  # 발급 시간
        'exp': datetime.utcnow() + timedelta(hours=24)  # 24시간 후 만료
    }
    
    # JWT 토큰 생성
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    print("🔑 테스트 유저 JWT 토큰 (24시간 유효):")
    print(f"Bearer {token}")
    print()
    print("📋 토큰 정보:")
    print(f"- 사용자 ID: {payload['sub']}")
    print(f"- 사용자명: {payload['username']}")
    print(f"- 이메일: {payload['email']}")
    print(f"- 발급 시간: {payload['iat']}")
    print(f"- 만료 시간: {payload['exp']}")
    
    return token

if __name__ == '__main__':
    generate_test_token()
