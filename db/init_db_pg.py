import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from config import (
    DJIA_COMPANIES_CSV,
    DJIA_PRICES_CSV,
)
from db.pg import get_engine


def normalize_companies(df: pd.DataFrame) -> pd.DataFrame:
    column_mapping = {}
    if "52_week_high" in df.columns:
        column_mapping["52_week_high"] = "week_52_high"
    if "52_week_low" in df.columns:
        column_mapping["52_week_low"] = "week_52_low"
    # Normalize common names
    if "Symbol" in df.columns:
        column_mapping["Symbol"] = "symbol"
    if "Name" in df.columns:
        column_mapping["Name"] = "name"
    if column_mapping:
        df = df.rename(columns=column_mapping)
    return df


def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
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
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    # Ensure datetime and numeric types
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    for col in ["open", "high", "low", "close", "dividends", "stock_splits"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    return df


def create_indexes(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date)"))


def load_to_postgres():
    engine = get_engine()
    companies_df = pd.read_csv(DJIA_COMPANIES_CSV)
    prices_df = pd.read_csv(DJIA_PRICES_CSV)

    companies_df = normalize_companies(companies_df)
    prices_df = normalize_prices(prices_df)

    # Write tables
    companies_df.to_sql("companies", engine, if_exists="replace", index=False, method="multi", chunksize=5000)
    prices_df.to_sql("prices", engine, if_exists="replace", index=False, method="multi", chunksize=5000)

    create_indexes(engine)

    # Quick counts
    with engine.connect() as conn:
        companies_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
        prices_count = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar() or 0
        print(f"Companies: {companies_count}, Prices: {prices_count}")


if __name__ == "__main__":
    load_to_postgres()

