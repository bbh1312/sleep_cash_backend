-- 중간 포인트 획득 로그 테이블
CREATE TABLE sleep_intermediate_claims (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sleep_log_id INTEGER NOT NULL,
    claim_sequence INTEGER NOT NULL,
    points_awarded DECIMAL(10,1) DEFAULT 10.0,
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (sleep_log_id) REFERENCES sleep_logs(id),
    UNIQUE(sleep_log_id, claim_sequence)
);

-- 인덱스 생성
CREATE INDEX idx_sleep_intermediate_claims_user ON sleep_intermediate_claims(user_id);
CREATE INDEX idx_sleep_intermediate_claims_session ON sleep_intermediate_claims(sleep_log_id);
