-- 슬립캐시 데이터베이스 스키마 (PostgreSQL - IDENTITY 적용)

-- 사용자 테이블
CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    total_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 수면 로그 테이블
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

-- 일일 수면 포인트 뱅크 테이블
CREATE TABLE daily_sleep_point_banks (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date_key VARCHAR(10) NOT NULL,
    pending_points DECIMAL(10,1) DEFAULT 0.0,
    claimed_points DECIMAL(10,1) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date_key)
);

-- 포인트 로그 테이블
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

-- 상품 테이블
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

-- 주문 테이블
CREATE TABLE orders (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 주문 상품 테이블
CREATE TABLE order_items (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 인덱스 생성
CREATE INDEX idx_sleep_logs_user_status ON sleep_logs(user_id, status);
CREATE INDEX idx_sleep_logs_user_awarded ON sleep_logs(user_id, awarded_minutes);
CREATE INDEX idx_daily_sleep_point_banks_user_date ON daily_sleep_point_banks(user_id, date_key);
CREATE INDEX idx_user_point_logs_user ON user_point_logs(user_id);
CREATE INDEX idx_orders_user ON orders(user_id);
