import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine

from config import (
    POSTGRES_CONFIG,
    DJIA_COMPANIES_CSV, 
    DJIA_PRICES_CSV,
    COMPANIES_TABLE_SCHEMA,
    PRICES_TABLE_SCHEMA,
    DB_CONNECTION_STRING,
)

def create_database():
    """Tạo database và import dữ liệu từ CSV"""
    
    # Kết nối PostgreSQL database
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    except psycopg2.OperationalError as e:
        print(f"Lỗi kết nối PostgreSQL: {e}")
        print(f"Vui lòng kiểm tra config: {POSTGRES_CONFIG}")
        return
    
    engine = None
    try:
        # Tạo bảng companies
        cursor.execute(COMPANIES_TABLE_SCHEMA)
        
        # Tạo bảng prices
        cursor.execute(PRICES_TABLE_SCHEMA)
        
        # Import dữ liệu companies
        print("Đang import dữ liệu companies...")
        companies_df = pd.read_csv(DJIA_COMPANIES_CSV)
        
        # Đổi tên cột để khớp với schema
        column_mapping = {}
        if "52_week_high" in companies_df.columns:
            column_mapping["52_week_high"] = "week_52_high"
        if "52_week_low" in companies_df.columns:
            column_mapping["52_week_low"] = "week_52_low"
        
        if column_mapping:
            companies_df = companies_df.rename(columns=column_mapping)
        
        # Đồng bộ schema: chỉ giữ các cột đúng định nghĩa và thêm cột còn thiếu
        company_columns = [
            "symbol", "name", "sector", "industry", "country", "website",
            "market_cap", "pe_ratio", "dividend_yield", "week_52_high",
            "week_52_low", "description"
        ]
        for col in company_columns:
            if col not in companies_df.columns:
                companies_df[col] = None
        companies_df = companies_df[company_columns]
        
        # Xóa dữ liệu cũ
        cursor.execute("DELETE FROM companies")
        conn.commit()
        
        # Import dữ liệu vào PostgreSQL
        if engine is None:
            engine = create_engine(DB_CONNECTION_STRING)
        companies_df.to_sql('companies', engine, if_exists='append', index=False, method='multi')
        print(f"Đã import {len(companies_df)} records vào bảng companies")
        
        # Import dữ liệu prices
        print("Đang import dữ liệu prices...")
        prices_df = pd.read_csv(DJIA_PRICES_CSV)
        
        # Đổi tên cột để khớp schema
        price_column_mapping = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Dividends": "dividends",
            "Stock Splits": "stock_splits",
            "Ticker": "ticker",
        }
        prices_df = prices_df.rename(columns={
            old: new for old, new in price_column_mapping.items()
            if old in prices_df.columns
        })
        
        # Chuẩn hoá ngày về định dạng DATE (PostgreSQL)
        if "date" in prices_df.columns:
            parsed_dates = pd.to_datetime(
                prices_df["date"],
                errors="coerce",
                utc=True,
            )
            parsed_dates = parsed_dates.dt.tz_localize(None)
            prices_df["date"] = parsed_dates.dt.date
        
        required_price_columns = [
            "date", "open", "high", "low", "close",
            "volume", "dividends", "stock_splits", "ticker"
        ]
        for col in required_price_columns:
            if col not in prices_df.columns:
                default_value = 0 if col in {"volume", "dividends", "stock_splits"} else None
                prices_df[col] = default_value
        
        prices_df = prices_df[required_price_columns]
        
        # Xóa dữ liệu cũ
        cursor.execute("DELETE FROM prices")
        conn.commit()
        
        # Import dữ liệu vào PostgreSQL
        if engine is None:
            engine = create_engine(DB_CONNECTION_STRING)
        prices_df.to_sql('prices', engine, if_exists='append', index=False, method='multi')
        print(f"Đã import {len(prices_df)} records vào bảng prices")
        
        # Tạo index để tăng tốc độ truy vấn
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date)")
        
        conn.commit()
        print("Database đã được tạo thành công!")
        
        # Hiển thị thông tin database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        print(f"Các bảng trong database: {[table[0] for table in tables]}")
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        companies_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM prices")
        prices_count = cursor.fetchone()[0]
        
        print(f"Số lượng companies: {companies_count}")
        print(f"Số lượng prices: {prices_count}")
        
    except Exception as e:
        print(f"Lỗi khi tạo database: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        if engine is not None:
            engine.dispose()
        if conn:
        conn.close()

if __name__ == "__main__":
    create_database()
