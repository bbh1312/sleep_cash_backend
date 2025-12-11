-- 중간 획득 포인트 시스템 추가

-- daily_sleep_point_banks 테이블에 중간 획득 관련 필드 추가
ALTER TABLE daily_sleep_point_banks 
ADD COLUMN intermediate_claimed_count INTEGER DEFAULT 0,
ADD COLUMN intermediate_claimed_points DECIMAL(10,1) DEFAULT 0.0;

-- 중간 포인트 획득 로그 테이블 생성
CREATE TABLE sleep_intermediate_claims (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sleep_log_id INTEGER NOT NULL,
    claim_sequence INTEGER NOT NULL, -- 1~5번째 획득
    points_awarded DECIMAL(10,1) DEFAULT 10.0,
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (sleep_log_id) REFERENCES sleep_logs(id),
    UNIQUE(sleep_log_id, claim_sequence)
);

-- 인덱스 추가
CREATE INDEX idx_sleep_intermediate_claims_user ON sleep_intermediate_claims(user_id);
CREATE INDEX idx_sleep_intermediate_claims_session ON sleep_intermediate_claims(sleep_log_id);
