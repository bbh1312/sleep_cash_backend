-- PostgreSQL용 수면 테이블 마이그레이션

-- 기존 sleep_logs 테이블에 awarded_minutes 필드 추가
ALTER TABLE sleep_logs ADD COLUMN awarded_minutes INTEGER DEFAULT 0;

-- DailySleepPointBank 테이블 생성
CREATE TABLE daily_sleep_point_banks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date_key VARCHAR(10) NOT NULL, -- YYYY-MM-DD 형태 (정오 기준)
    pending_points DECIMAL(10,1) DEFAULT 0.0,
    claimed_points DECIMAL(10,1) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date_key)
);

-- 인덱스 추가
CREATE INDEX idx_daily_sleep_point_banks_user_date ON daily_sleep_point_banks(user_id, date_key);
CREATE INDEX idx_sleep_logs_user_awarded ON sleep_logs(user_id, awarded_minutes);

-- user_point_logs 테이블에 source 필드 추가 (sleep 포인트 구분용)
ALTER TABLE user_point_logs ADD COLUMN source VARCHAR(20) DEFAULT 'general';
