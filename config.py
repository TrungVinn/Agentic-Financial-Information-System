"""
Configuration file for DJIA Multi-Agent System.

Định nghĩa các đường dẫn và schema database cho hệ thống.
"""

from pathlib import Path

# ==================== ĐƯỜNG DẪN DỰ ÁN ====================

# Thư mục gốc của project
PROJECT_ROOT = Path(__file__).parent

# Thư mục chứa dữ liệu CSV và SQL samples
DATA_DIR = PROJECT_ROOT / "data"

# Thư mục chứa database SQLite
DB_DIR = PROJECT_ROOT / "db"


# ==================== DATABASE ====================

# Đường dẫn đến SQLite database chính
# Database này lưu trữ:
# - Thông tin 30 công ty DJIA (bảng companies)
# - Dữ liệu giá cổ phiếu lịch sử (bảng prices)
DB_PATH = DB_DIR / "djia.db"


# ==================== DỮ LIỆU ĐẦU VÀO ====================

# File CSV chứa thông tin công ty (symbol, name, sector, industry...)
DJIA_COMPANIES_CSV = DATA_DIR / "djia_companies_20250426.csv"

# File CSV chứa dữ liệu giá cổ phiếu (date, open, high, low, close, volume...)
DJIA_PRICES_CSV = DATA_DIR / "djia_prices_20250426.csv"

# File chứa 80+ SQL templates mẫu
# Được sử dụng bởi SQL Template Matcher để tìm SQL phù hợp với câu hỏi
SQL_SAMPLES_FILE = DATA_DIR / "sql_samples.sql"


# ==================== DATABASE SCHEMA ====================

# Schema cho bảng companies
# Lưu trữ thông tin cơ bản và tài chính của 30 công ty DJIA
COMPANIES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    symbol TEXT,              -- Mã cổ phiếu (AAPL, MSFT, ...)
    name TEXT,                -- Tên công ty đầy đủ
    sector TEXT,              -- Ngành (Technology, Healthcare, ...)
    industry TEXT,            -- Lĩnh vực cụ thể
    country TEXT,             -- Quốc gia
    website TEXT,             -- Website công ty
    market_cap REAL,          -- Vốn hóa thị trường
    pe_ratio REAL,            -- Tỷ lệ giá/thu nhập
    dividend_yield REAL,      -- Lợi suất cổ tức
    week_52_high REAL,        -- Giá cao nhất 52 tuần
    week_52_low REAL,         -- Giá thấp nhất 52 tuần
    description TEXT          -- Mô tả công ty
);
"""

# Schema cho bảng prices
# Lưu trữ dữ liệu giá cổ phiếu theo ngày
PRICES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    date TEXT,                -- Ngày giao dịch (YYYY-MM-DD)
    open REAL,                -- Giá mở cửa
    high REAL,                -- Giá cao nhất trong ngày
    low REAL,                 -- Giá thấp nhất trong ngày
    close REAL,               -- Giá đóng cửa
    volume INTEGER,           -- Khối lượng giao dịch
    dividends REAL,           -- Cổ tức (nếu có)
    stock_splits REAL,        -- Tỷ lệ chia tách cổ phiếu (nếu có)
    ticker TEXT               -- Mã cổ phiếu (AAPL, MSFT, ...)
);
"""
