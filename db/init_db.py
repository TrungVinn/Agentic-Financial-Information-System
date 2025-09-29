import sqlite3
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import (
    DB_PATH, 
    DJIA_COMPANIES_CSV, 
    DJIA_PRICES_CSV,
    COMPANIES_TABLE_SCHEMA,
    PRICES_TABLE_SCHEMA
)

def create_database():
    """Tạo database và import dữ liệu từ CSV"""
    
    # Tạo thư mục db nếu chưa có
    DB_PATH.parent.mkdir(exist_ok=True)
    
    # Kết nối database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Tạo bảng companies
        cursor.execute(COMPANIES_TABLE_SCHEMA)
        
        # Tạo bảng prices
        cursor.execute(PRICES_TABLE_SCHEMA)
        
        # Import dữ liệu companies
        print("Đang import dữ liệu companies...")
        companies_df = pd.read_csv(DJIA_COMPANIES_CSV)
        
        # Đổi tên cột để khớp với schema mới
        column_mapping = {}
        if "52_week_high" in companies_df.columns:
            column_mapping["52_week_high"] = "week_52_high"
        if "52_week_low" in companies_df.columns:
            column_mapping["52_week_low"] = "week_52_low"
        
        if column_mapping:
            companies_df = companies_df.rename(columns=column_mapping)
        
        companies_df.to_sql('companies', conn, if_exists='replace', index=False)
        print(f"Đã import {len(companies_df)} records vào bảng companies")
        
        # Import dữ liệu prices
        print("Đang import dữ liệu prices...")
        prices_df = pd.read_csv(DJIA_PRICES_CSV)
        
        # Đổi tên cột Ticker thành ticker để khớp với schema
        if "Ticker" in prices_df.columns:
            prices_df = prices_df.rename(columns={"Ticker": "ticker"})
        
        prices_df.to_sql('prices', conn, if_exists='replace', index=False)
        print(f"Đã import {len(prices_df)} records vào bảng prices")
        
        # Tạo index để tăng tốc độ truy vấn
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date)")
        
        conn.commit()
        print("Database đã được tạo thành công!")
        
        # Hiển thị thông tin database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
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
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
