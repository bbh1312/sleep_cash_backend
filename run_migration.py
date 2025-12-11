#!/usr/bin/env python3
"""
수면 테이블 마이그레이션 실행 스크립트
"""
import sqlite3
import os

def run_migration():
    db_path = 'instance/sleepcash.db'
    
    if not os.path.exists(db_path):
        print("데이터베이스 파일이 없습니다. 먼저 앱을 실행해주세요.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 마이그레이션 SQL 실행
        with open('migrations/001_update_sleep_tables.sql', 'r') as f:
            sql_commands = f.read().split(';')
            
        for command in sql_commands:
            command = command.strip()
            if command:
                print(f"실행 중: {command[:50]}...")
                cursor.execute(command)
        
        conn.commit()
        print("✅ 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
