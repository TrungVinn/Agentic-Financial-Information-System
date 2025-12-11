"""
Configuration file for DJIA Multi-Agent System.

Định nghĩa các đường dẫn và schema database cho hệ thống.
"""

from pathlib import Path
import os

# ==================== ĐƯỜNG DẪN DỰ ÁN ====================

# Thư mục gốc của project
PROJECT_ROOT = Path(__file__).parent

# Thư mục chứa dữ liệu CSV và SQL samples
DATA_DIR = PROJECT_ROOT / "data"


# ==================== DATABASE ====================

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "djia"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "admin"),
}

# Connection string cho SQLAlchemy
DB_CONNECTION_STRING = (
    f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}"
    f"@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
)


# ==================== DỮ LIỆU ĐẦU VÀO ====================

# File CSV chứa thông tin công ty (symbol, name, sector, industry...)
DJIA_COMPANIES_CSV = DATA_DIR / "djia_companies_20251210.csv"

# File CSV chứa dữ liệu giá cổ phiếu (date, open, high, low, close, volume...)
DJIA_PRICES_CSV = DATA_DIR / "djia_prices_20251210.csv"

# File chứa 80+ SQL templates mẫu
# Được sử dụng bởi SQL Template Matcher để tìm SQL phù hợp với câu hỏi
SQL_SAMPLES_FILE = DATA_DIR / "sql_samples.sql"


# ==================== DATABASE SCHEMA ====================

# Schema cho bảng companies (PostgreSQL)
# Lưu trữ thông tin cơ bản và tài chính của 30 công ty DJIA
COMPANIES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    symbol VARCHAR(10) PRIMARY KEY,    -- CSV column: symbol
    name TEXT,                         -- CSV column: name
    sector TEXT,                       -- CSV column: sector
    industry TEXT,                     -- CSV column: industry
    country TEXT,                      -- CSV column: country
    website TEXT,                      -- CSV column: website
    market_cap NUMERIC(24, 4),         -- CSV column: market_cap
    pe_ratio NUMERIC(18, 6),           -- CSV column: pe_ratio
    dividend_yield NUMERIC(18, 6),     -- CSV column: dividend_yield
    week_52_high NUMERIC(18, 4),       -- CSV column: 52_week_high (renamed)
    week_52_low NUMERIC(18, 4),        -- CSV column: 52_week_low (renamed)
    description TEXT                   -- CSV column: description
);
"""

# Schema cho bảng prices (PostgreSQL)
# Lưu trữ dữ liệu giá cổ phiếu theo ngày
PRICES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    date DATE,                         -- CSV column: Date (converted to date)
    open NUMERIC(18, 6),               -- CSV column: Open
    high NUMERIC(18, 6),               -- CSV column: High
    low NUMERIC(18, 6),                -- CSV column: Low
    close NUMERIC(18, 6),              -- CSV column: Close
    volume BIGINT,                     -- CSV column: Volume
    dividends NUMERIC(18, 6),          -- CSV column: Dividends
    stock_splits NUMERIC(18, 6),       -- CSV column: Stock Splits
    ticker VARCHAR(10),                -- CSV column: Ticker
    PRIMARY KEY (date, ticker)
);
"""
