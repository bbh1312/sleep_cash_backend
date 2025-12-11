-- 슬립캐시 데이터베이스 및 테이블 생성 스크립트 (중간 획득 포인트 포함)

-- 1. 사용자 및 데이터베이스 생성 (관리자 권한으로 실행)
CREATE ROLE sleepcashuser WITH LOGIN PASSWORD 'tmfflqzotl!@';
CREATE DATABASE sleep_cash OWNER sleepcashuser;

-- 2. sleep_cash 데이터베이스에 연결 후 아래 테이블들 생성

CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    total_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sleep_logs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    awarded_minutes INTEGER DEFAULT 0,
    total_sleep_minutes INTEGER,
    sleep_score INTEGER,
    mood VARCHAR(20),
    memo TEXT,
    white_noise_type VARCHAR(50),
    white_noise_volume INTEGER,
    status VARCHAR(20) DEFAULT 'running' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE daily_sleep_point_banks (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date_key VARCHAR(10) NOT NULL,
    pending_points DECIMAL(10,1) DEFAULT 0.0,
    claimed_points DECIMAL(10,1) DEFAULT 0.0,
    intermediate_claimed_count INTEGER DEFAULT 0,
    intermediate_claimed_points DECIMAL(10,1) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date_key)
);

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

CREATE TABLE user_point_logs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    change INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    source VARCHAR(20) DEFAULT 'general',
    sleep_log_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (sleep_log_id) REFERENCES sleep_logs(id)
);

CREATE TABLE products (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    image_url VARCHAR(255),
    category VARCHAR(50),
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_sleep_logs_user_status ON sleep_logs(user_id, status);
CREATE INDEX idx_sleep_logs_user_awarded ON sleep_logs(user_id, awarded_minutes);
CREATE INDEX idx_daily_sleep_point_banks_user_date ON daily_sleep_point_banks(user_id, date_key);
CREATE INDEX idx_sleep_intermediate_claims_user ON sleep_intermediate_claims(user_id);
CREATE INDEX idx_sleep_intermediate_claims_session ON sleep_intermediate_claims(sleep_log_id);
CREATE INDEX idx_user_point_logs_user ON user_point_logs(user_id);
CREATE INDEX idx_orders_user ON orders(user_id);
