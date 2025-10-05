from typing import Dict, Any, Optional, Tuple
import re
import sqlite3
import pandas as pd
from config import DB_PATH
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
    
    # Xử lý format "which had a higher closing price: A or B?"
    colon_or_match = re.search(r":\s*([^:]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if colon_or_match:
        company1 = colon_or_match.group(1).strip()
        company2 = colon_or_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            params["ticker_a"] = t1
            params["ticker_b"] = t2
    
    # Tìm pattern "company1 or company2" hoặc "company1 vs company2" - cẩn thận với "or" trong "higher"
    patterns = [
        r"([^,]+?)\s+or\s+([^,]+?)(?:\s+had|$)",  # "A or B had" hoặc "A or B"
        r"([^,]+?)\s+vs\s+([^,]+?)(?:\s+had|$)",   # "A vs B had" hoặc "A vs B"
        r"([^,]+?)\s+versus\s+([^,]+?)(?:\s+had|$)", # "A versus B had" hoặc "A versus B"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            company1 = match.group(1).strip().rstrip('?.,!')
            company2 = match.group(2).strip().rstrip('?.,!')
            t1 = extract_ticker(company1)
            t2 = extract_ticker(company2)
            if t1 and t2:
                params["ticker_a"] = t1
                params["ticker_b"] = t2
                break
    return params

def run_sql(sql: str, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """Thực thi SQL (giữ nguyên bind params) và trả về SQL hiển thị đã thay thế."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # Bản hiển thị: thay :param bằng giá trị để SHOW, không dùng để execute
        display_sql = sql
        # Sắp xếp params theo độ dài để tránh thay thế sai (ticker_a trước ticker)
        sorted_params = sorted(params.items(), key=lambda x: len(x[0]), reverse=True)
        for param_name, param_value in sorted_params:
            if isinstance(param_value, str):
                display_sql = display_sql.replace(f":{param_name}", f"'{param_value}'")
            else:
                display_sql = display_sql.replace(f":{param_name}", str(param_value))
        display_sql = "\n".join(
            [line for line in display_sql.splitlines() if not line.strip().startswith("--")]
        ).strip()

        # Thực thi bằng SQL gốc + params
        df = pd.read_sql_query(sql, conn, params=params)
        return df, display_sql
    finally:
        conn.close()

def execute_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    ticker = state.get("ticker")
    sql = state.get("sql") or ""
    params = build_params(question, ticker)
    try:
        df, actual_sql = run_sql(sql, params)
        return {**state, "df": df, "actual_sql": actual_sql, "error": None}
    except Exception as e:
        # trả feedback cho node LLM chỉnh sửa nếu có bước retry
        return {**state, "df": pd.DataFrame(), "actual_sql": sql, "error": str(e), "feedback": f"{e}. SQL: {sql}"}


