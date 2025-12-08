"""
SQL Executor Node - Thực thi SQL trên PostgreSQL database.

Module này thực hiện:
1. Build parameters từ câu hỏi (ticker, date, year, quarter...)
2. Thực thi SQL với bind parameters
3. Trả về DataFrame kết quả và SQL đã được format để hiển thị
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_CONNECTION_STRING, POSTGRES_CONFIG
from nodes.utils import (
    normalize_text,
    extract_date_parts,
    extract_date_range,
    extract_quarter,
    extract_month_range,
    extract_ticker,
)


def build_params(
    question: str, ticker: Optional[str], state: Optional[Dict[str, Any]] = None
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

    # ========== XỬ LÝ CÂU HỎI TÌM TICKER SYMBOL ==========
    # Ví dụ: "What is the ticker symbol for Walt Disney?" hoặc "symbol of apple"
    # Pattern: "ticker symbol for {company}", "symbol for {company}", "symbol of {company}", "ticket of {company}"
    ticker_symbol_patterns = [
        r"ticker\s+symbol\s+for\s+([^?]+)",
        r"symbol\s+for\s+([^?]+)",
        r"ticker\s+of\s+([^?]+)",
        r"symbol\s+of\s+([^?]+)",
        r"ticket\s+of\s+([^?]+)",  # "ticket" (typo của "ticker")
    ]
    for pattern in ticker_symbol_patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            company_name = match.group(1).strip().rstrip("?.,!")
            # Luôn extract company name cho câu hỏi tìm ticker symbol
            if company_name:
                params["company"] = company_name
            break

    # Nếu chưa có company nhưng câu hỏi về ticker symbol và có ticker,
    # thử extract tên công ty từ câu hỏi (fallback)
    if "company" not in params and ticker:
        q_lower = normalize_text(question)
        # Kiểm tra xem có phải câu hỏi về ticker symbol không
        is_ticker_symbol_query = any(
            phrase in q_lower
            for phrase in [
                "ticker symbol",
                "symbol of",
                "ticket of",
                "ticker of",
                "mã cổ phiếu",
                "mã ticker",
            ]
        )
        if is_ticker_symbol_query:
            # Thử extract tên công ty từ các pattern khác
            # Pattern: "what is the ticker symbol for {company}?"
            # Hoặc: "symbol of {company}"
            fallback_patterns = [
                r"(?:what|which|tell me).*?(?:ticker|symbol|ticket).*?(?:of|for)\s+([^?]+)",
                r"(?:ticker|symbol|ticket).*?(?:of|for)\s+([^?]+)",
            ]
            for pattern in fallback_patterns:
                match = re.search(pattern, question, re.IGNORECASE)
                if match:
                    company_name = match.group(1).strip().rstrip("?.,!")
                    if company_name and len(company_name) > 0:
                        params["company"] = company_name
                        break

    # Extract company name từ pattern "X of {company}" cho các câu hỏi metadata
    # Ví dụ: "dividend yield of apple", "52 week high of apple"
    if "company" not in params:
        # Pattern: "{field} of {company}"
        metadata_patterns = [
            r"(\w+(?:\s+\w+)*)\s+of\s+([^?]+)",
        ]
        for pattern in metadata_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                field = match.group(1).strip()
                company_name = match.group(2).strip().rstrip("?.,!")
                # Kiểm tra xem field có phải là metadata field không
                metadata_fields = [
                    "dividend yield",
                    "52 week high",
                    "52 week low",
                    "week 52 high",
                    "week 52 low",
                    "market cap",
                    "pe ratio",
                    "p/e ratio",
                    "description",
                    "country",
                    "industry",
                    "sector",
                    "website",
                    "market capitalization",
                ]
                if any(mf in field.lower() for mf in metadata_fields):
                    if company_name and len(company_name) > 0:
                        params["company"] = company_name
                        break

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
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            total_days = max((end_dt - start_dt).days, 0)
            if total_days == 0:
                years_value = 1.0
            else:
                years_value = max(total_days / 365.0, 0.001)
            params["years"] = round(years_value, 6)
        except ValueError:
            pass
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
            company1 = match.group(1).strip().rstrip("?.,!")
            company2 = match.group(2).strip().rstrip("?.,!")
            t1 = extract_ticker(company1)
            t2 = extract_ticker(company2)
            if t1 and t2:
                params["ticker_a"] = t1
                params["ticker_b"] = t2
                break  # Tìm thấy rồi thì dừng

    # ========== XỬ LÝ CHART PARAMETERS ==========
    # Nếu cần vẽ biểu đồ, có thể có thêm parameters về date range
    chart_request = (
        (state or {}).get("chart_request") if isinstance(state, dict) else None
    )
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

    # ========== FALLBACK CHO :company ==========
    # Nếu SQL có parameter :company nhưng chưa được set,
    # thử trích xuất tên công ty từ câu hỏi
    if "company" not in params:
        sql_text = (state or {}).get("sql", "")
        if ":company" in sql_text or "%(company)s" in sql_text:
            # Danh sách tên công ty DJIA phổ biến
            company_names = {
                "apple": "Apple", "microsoft": "Microsoft", "amazon": "Amazon",
                "google": "Google", "alphabet": "Alphabet", "meta": "Meta",
                "nvidia": "NVIDIA", "tesla": "Tesla", "boeing": "Boeing",
                "disney": "Disney", "coca-cola": "Coca-Cola", "coca cola": "Coca-Cola",
                "mcdonald": "McDonald", "nike": "Nike", "walmart": "Walmart",
                "visa": "Visa", "jpmorgan": "JPMorgan", "intel": "Intel",
                "ibm": "IBM", "cisco": "Cisco", "verizon": "Verizon",
                "chevron": "Chevron", "caterpillar": "Caterpillar",
                "goldman sachs": "Goldman Sachs", "unitedhealth": "UnitedHealth",
                "home depot": "Home Depot", "amgen": "Amgen", "honeywell": "Honeywell",
                "3m": "3M", "travelers": "Travelers", "dow": "Dow",
                "salesforce": "Salesforce", "walgreens": "Walgreens",
                "american express": "American Express", "merck": "Merck",
            }
            q_lower = question.lower()
            for name_key, name_value in company_names.items():
                if name_key in q_lower:
                    params["company"] = name_value
                    break

    return params


def run_sql(sql: str, params: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
    """
    Thực thi SQL trên PostgreSQL database với bind parameters.

    Hàm này:
    1. Kết nối đến PostgreSQL database
    2. Thực thi SQL với parameters (để tránh SQL injection)
    3. Tạo SQL hiển thị (thay %(params)s bằng giá trị thực) để show cho user
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
        psycopg2.Error: Nếu SQL không hợp lệ hoặc lỗi database
    """
    # SQL samples/LLM output đã ở dạng PostgreSQL nên chỉ cần dùng trực tiếp
    pg_sql = sql

    # Kết nối đến PostgreSQL database
    engine = create_engine(DB_CONNECTION_STRING)

    try:
        # ========== TẠO SQL HIỂN THỊ ==========
        # Thay :param và %(param)s bằng giá trị thực để show cho user
        # KHÔNG dùng SQL này để execute (dùng SQL gốc với params để tránh SQL injection)
        display_sql = pg_sql

        # Sắp xếp params theo độ dài để tránh thay thế sai (thay thế param dài trước)
        sorted_params = sorted(params.items(), key=lambda x: len(x[0]), reverse=True)

        for param_name, param_value in sorted_params:
            # Format giá trị để hiển thị
            if isinstance(param_value, str):
                # String parameters cần có dấu nháy
                formatted_value = f"'{param_value}'"
            elif param_value is None:
                formatted_value = "NULL"
            else:
                # Số không cần dấu nháy
                formatted_value = str(param_value)

            # Thay thế cả :param và %(param)s
            # Dùng regex để tránh thay thế nhầm (ví dụ :ticker trong :ticker_a)
            # Pattern: :param_name không phải là phần của từ khác
            pattern1 = r":\b" + re.escape(param_name) + r"\b"
            display_sql = re.sub(pattern1, formatted_value, display_sql)
            # Pattern: %(param_name)s
            pattern2 = r"%\(" + re.escape(param_name) + r"\)s"
            display_sql = re.sub(pattern2, formatted_value, display_sql)

        # Loại bỏ comment lines để SQL hiển thị gọn gàng
        display_sql = "\n".join(
            [
                line
                for line in display_sql.splitlines()
                if not line.strip().startswith("--")
            ]
        ).strip()

        # ========== THỰC THI SQL ==========
        # Dùng SQL đã convert với bind parameters (an toàn, tránh SQL injection)
        with engine.connect() as conn:
            df = pd.read_sql_query(text(pg_sql), conn, params=params)

        return df, display_sql

    finally:
        engine.dispose()


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
            "feedback": None,
        }

    except Exception as e:
        # Xử lý lỗi: trả về empty DataFrame và error message
        # Feedback được dùng để retry với LLM (nếu workflow có bước retry)
        return {
            **state,
            "df": pd.DataFrame(),
            "actual_sql": sql,
            "error": str(e),
            "feedback": f"{e}. SQL: {sql}",
        }
