#!/usr/bin/env python3
"""
PostgreSQL 테이블 생성 스크립트
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    # 환경변수에서 DB 정보 가져오기
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'sleepcash'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 스키마 파일 읽기
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # SQL 명령어들을 분리하여 실행
        commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]
        
        for command in commands:
            if command:
                print(f"실행 중: {command[:50]}...")
                cursor.execute(command)
        
        conn.commit()
        print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    create_tables()
