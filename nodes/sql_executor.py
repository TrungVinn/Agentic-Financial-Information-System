from typing import Dict, Any, Optional
import re
import pandas as pd
from sqlalchemy import text
from db.pg import get_engine
from nodes.utils import normalize_text, extract_date_parts, extract_date_range, extract_quarter, extract_month_range, extract_ticker

def build_params(question: str, ticker: Optional[str]) -> Dict[str, Any]:
    parts = extract_date_parts(question)
    start_date, end_date = extract_date_range(question)
    quarter = extract_quarter(question)
    start_month, end_month = extract_month_range(question)
    params: Dict[str, Any] = {}
    if ticker:
        params["ticker"] = ticker
        params["ticker_a"] = ticker
    if "date" in parts:
        params["date"] = parts["date"]
    if "year" in parts:
        params["year"] = parts["year"]
    if "month" in parts:
        params["month"] = parts["month"]
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if quarter:
        params["quarter"] = quarter
    if start_month:
        params["start_month"] = start_month
    if end_month:
        params["end_month"] = end_month
    # Thử bắt hai công ty dạng "A or B" hoặc "A vs B"
    q = normalize_text(question)
    vs = re.split(r"\bvs\b|\bversus\b|\bor\b|\bso sánh\b", q)
    if len(vs) >= 2:
        t1 = extract_ticker(vs[0])
        t2 = extract_ticker(vs[1])
        if t1:
            params["ticker_a"] = t1
        if t2:
            params["ticker_b"] = t2
    return params

def run_sql(sql: str, params: Dict[str, Any]) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn, params=params)
        return df

def execute_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    ticker = state.get("ticker")
    sql = state.get("sql") or ""
    params = build_params(question, ticker)
    try:
        df = run_sql(sql, params)
        return {**state, "df": df, "error": None}
    except Exception as e:
        # trả feedback cho node LLM chỉnh sửa nếu có bước retry
        return {**state, "df": pd.DataFrame(), "error": str(e), "feedback": f"{e}. SQL: {sql}"}


