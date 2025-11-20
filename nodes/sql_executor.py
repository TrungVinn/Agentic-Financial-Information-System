"""
SQL Executor Node - Thực thi SQL trên SQLite database.

Module này thực hiện:
1. Build parameters từ câu hỏi (ticker, date, year, quarter...)
2. Thực thi SQL với bind parameters
3. Trả về DataFrame kết quả và SQL đã được format để hiển thị
"""

from typing import Dict, Any, Optional, Tuple
import re
import sqlite3
import pandas as pd
from config import DB_PATH
from nodes.utils import (
    normalize_text,
    extract_date_parts,
    extract_date_range,
    extract_quarter,
    extract_month_range,
    extract_ticker
)


def build_params(
    question: str,
    ticker: Optional[str],
    state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Xây dựng dictionary parameters từ câu hỏi để bind vào SQL.
    
    Hàm này trích xuất các thông tin từ câu hỏi như:
    - Ticker/symbol công ty
    - Ngày cụ thể, khoảng ngày
    - Năm, tháng, quý
    - Hai công ty (cho câu hỏi so sánh)
    
    Args:
        question: Câu hỏi từ người dùng
        ticker: Mã cổ phiếu đã được trích xuất (nếu có)
        state: State từ workflow (có thể chứa thông tin bổ sung)
        
    Returns:
        Dictionary với các key như:
        - ticker, ticker_a, ticker_b: Mã cổ phiếu
        - date: Ngày cụ thể (YYYY-MM-DD)
        - year: Năm (YYYY)
        - month: Tháng (MM)
        - quarter: Quý (1-4)
        - start_date, end_date: Khoảng ngày
        - start_month, end_month: Khoảng tháng
        - window_days: Số ngày cho window queries
        
    Examples:
        >>> build_params("What was Apple's closing price on 2024-01-15?", "AAPL")
        {'ticker': 'AAPL', 'date': '2024-01-15'}
        
        >>> build_params("Average price in Q1 2024?", "AAPL")
        {'ticker': 'AAPL', 'year': '2024', 'quarter': 1}
    """
    # Trích xuất các thành phần ngày tháng từ câu hỏi
    parts = extract_date_parts(question)
    start_date, end_date = extract_date_range(question)
    quarter = extract_quarter(question)
    start_month, end_month = extract_month_range(question)
    
    # Khởi tạo params dictionary
    params: Dict[str, Any] = {}
    
    # Thêm ticker (dùng cho both single và comparative queries)
    if ticker:
        params["ticker"] = ticker
        params["ticker_a"] = ticker  # Cho comparative queries
    
    # Thêm date/time parameters
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
    
    # ========== XỬ LÝ CÂU HỎI SO SÁNH 2 CÔNG TY ==========
    # Ví dụ: "Which had a higher closing price: Apple or Microsoft?"
    
    q = normalize_text(question)
    
    # Pattern 1: "which had a higher closing price: A or B?"
    colon_or_match = re.search(r":\s*([^:]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if colon_or_match:
        company1 = colon_or_match.group(1).strip()
        company2 = colon_or_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            params["ticker_a"] = t1
            params["ticker_b"] = t2
    
    # Pattern 2-4: "A or B", "A vs B", "A versus B"
    patterns = [
        r"([^,]+?)\s+or\s+([^,]+?)(?:\s+had|$)",
        r"([^,]+?)\s+vs\s+([^,]+?)(?:\s+had|$)",
        r"([^,]+?)\s+versus\s+([^,]+?)(?:\s+had|$)",
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
                break  # Tìm thấy rồi thì dừng
    
    # ========== XỬ LÝ CHART PARAMETERS ==========
    # Nếu cần vẽ biểu đồ, có thể có thêm parameters về date range
    chart_request = (state or {}).get("chart_request") if isinstance(state, dict) else None
    if chart_request:
        if chart_request.get("start_date"):
            params["start_date"] = chart_request["start_date"]
        if chart_request.get("end_date"):
            params["end_date"] = chart_request["end_date"]
        if chart_request.get("use_recent_window"):
            params["window_days"] = int(chart_request.get("window_days", 180))
    
    # ========== FALLBACK CHO :window_days ==========
    # Nếu SQL có parameter :window_days nhưng chưa được set,
    # dùng giá trị mặc định 180 ngày
    # (Xảy ra khi LLM sinh SQL không đúng format)
    if "window_days" not in params:
        sql_text = (state or {}).get("sql", "")
        if ":window_days" in sql_text:
            params["window_days"] = 180  # ~6 tháng
    
    return params


def run_sql(sql: str, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Thực thi SQL trên SQLite database với bind parameters.
    
    Hàm này:
    1. Kết nối đến SQLite database
    2. Thực thi SQL với parameters (để tránh SQL injection)
    3. Tạo SQL hiển thị (thay :params bằng giá trị thực) để show cho user
    4. Trả về DataFrame kết quả và SQL đã format
    
    Args:
        sql: Câu lệnh SQL với bind parameters (:ticker, :date, ...)
        params: Dictionary parameters để bind vào SQL
        
    Returns:
        Tuple gồm:
        - DataFrame: Kết quả truy vấn
        - String: SQL đã thay thế parameters để hiển thị
        
    Examples:
        >>> sql = "SELECT * FROM prices WHERE ticker = :ticker AND date = :date"
        >>> params = {"ticker": "AAPL", "date": "2024-01-15"}
        >>> df, display_sql = run_sql(sql, params)
        >>> print(display_sql)
        SELECT * FROM prices WHERE ticker = 'AAPL' AND date = '2024-01-15'
        
    Raises:
        sqlite3.Error: Nếu SQL không hợp lệ hoặc lỗi database
    """
    # Kết nối đến SQLite database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # ========== TẠO SQL HIỂN THỊ ==========
        # Thay :param bằng giá trị thực để show cho user
        # KHÔNG dùng SQL này để execute (dùng SQL gốc với params để tránh SQL injection)
        display_sql = sql
        
        # Sắp xếp params theo độ dài để tránh thay thế sai
        # Ví dụ: ticker_a phải thay trước ticker (tránh nhầm ticker_a thành AAPL_a)
        sorted_params = sorted(params.items(), key=lambda x: len(x[0]), reverse=True)
        
        for param_name, param_value in sorted_params:
            if isinstance(param_value, str):
                # String parameters cần có dấu nháy
                display_sql = display_sql.replace(f":{param_name}", f"'{param_value}'")
            else:
                # Số không cần dấu nháy
                display_sql = display_sql.replace(f":{param_name}", str(param_value))
        
        # Loại bỏ comment lines để SQL hiển thị gọn gàng
        display_sql = "\n".join(
            [line for line in display_sql.splitlines() if not line.strip().startswith("--")]
        ).strip()
        
        # ========== THỰC THI SQL ==========
        # Dùng SQL gốc với bind parameters (an toàn, tránh SQL injection)
        df = pd.read_sql_query(sql, conn, params=params)
        
        return df, display_sql
        
    finally:
        # Đảm bảo đóng connection
        conn.close()


def execute_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Thực thi SQL và trả về kết quả.
    
    Đây là node quan trọng trong workflow, thực hiện:
    1. Build parameters từ câu hỏi
    2. Thực thi SQL trên database
    3. Trả về DataFrame kết quả hoặc error message
    
    Args:
        state: Dictionary chứa workflow state, cần có:
        - question: Câu hỏi từ người dùng
        - ticker: Mã cổ phiếu (optional)
        - sql: Câu lệnh SQL cần thực thi
        
    Returns:
        State mới với các key bổ sung:
        - df: DataFrame kết quả (hoặc empty nếu lỗi)
        - actual_sql: SQL đã thay thế parameters để hiển thị
        - error: Error message (None nếu thành công)
        - feedback: Feedback để retry (nếu có lỗi)
        
    Note:
        Nếu SQL execution thất bại, trả về empty DataFrame và error message
        để node tiếp theo có thể xử lý (ví dụ: retry với LLM)
    """
    # Lấy thông tin từ state
    question = state.get("question", "")
    ticker = state.get("ticker")
    sql = state.get("sql") or ""
    
    # Build parameters từ câu hỏi
    params = build_params(question, ticker, state)
    
    try:
        # Thực thi SQL
        df, actual_sql = run_sql(sql, params)
        
        # Trả về kết quả thành công
        return {
            **state,
            "df": df,
            "actual_sql": actual_sql,
            "error": None,
            "feedback": None
        }
        
    except Exception as e:
        # Xử lý lỗi: trả về empty DataFrame và error message
        # Feedback được dùng để retry với LLM (nếu workflow có bước retry)
        return {
            **state,
            "df": pd.DataFrame(),
            "actual_sql": sql,
            "error": str(e),
            "feedback": f"{e}. SQL: {sql}"
        }
