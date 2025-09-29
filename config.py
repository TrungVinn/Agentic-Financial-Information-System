from pathlib import Path
import os

# Đường dẫn dự án
PROJECT_ROOT = Path(__file__).parent

# Đường dẫn dữ liệu/DB
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "db"
# SQLite path kept for backward compatibility; not used when PostgreSQL is configured
DB_PATH = DB_DIR / "djia.db"
DATABASE_URL = os.getenv("DATABASE_URL", "")

DJIA_COMPANIES_CSV = DATA_DIR / "djia_companies_20250426.csv"
DJIA_PRICES_CSV = DATA_DIR / "djia_prices_20250426.csv"
SQL_SAMPLES_FILE = DATA_DIR / "sql_samples.sql"


# Schema bảng companies và prices cho SQLite
COMPANIES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    symbol TEXT,
    name TEXT,
    sector TEXT,
    industry TEXT,
    country TEXT,
    website TEXT,
    market_cap REAL,
    pe_ratio REAL,
    dividend_yield REAL,
    week_52_high REAL,
    week_52_low REAL,
    description TEXT
);
"""

PRICES_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    dividends REAL,
    stock_splits REAL,
    ticker TEXT
);
"""


