from typing import Dict, Any, Optional
import os
from google import genai as google_genai
from dotenv import load_dotenv

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

def generate_sql_with_llm(question: str, feedback: Optional[str] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = google_genai.Client(api_key=api_key)
    system = (
        "Bạn là trợ lý tạo SQL cho PostgreSQL. Có 2 bảng:\n"
        "- prices(date TIMESTAMPTZ, open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION, close DOUBLE PRECISION, volume BIGINT, dividends DOUBLE PRECISION, stock_splits DOUBLE PRECISION, ticker TEXT)\n"
        "- companies(symbol TEXT, name TEXT, sector TEXT, industry TEXT, country TEXT, website TEXT, market_cap DOUBLE PRECISION, pe_ratio DOUBLE PRECISION, dividend_yield DOUBLE PRECISION, week_52_high DOUBLE PRECISION, week_52_low DOUBLE PRECISION, description TEXT)\n\n"
        "Quy tắc bắt buộc:\n"
        "- Trả về CHỈ MỘT câu SQL hợp lệ cho PostgreSQL.\n"
        "- Dùng tham số kiểu :ticker, :date, :year, :month, :quarter nếu phù hợp.\n"
        "- So sánh theo ngày dùng DATE(date) = DATE(:date).\n"
        "- Lọc theo năm dùng to_char(date, 'YYYY') = :year (hoặc EXTRACT(YEAR FROM date) = :year).\n"
        "- Lọc theo tháng dùng to_char(date, 'MM') = :month.\n"
        "- Không thêm giải thích hay markdown.\n"
    )
    if feedback:
        prompt_text = (
            f"{system}\nCâu hỏi: {question}\n\nLỗi khi chạy SQL trước đó, hãy sửa câu lệnh: {feedback}"
        )
    else:
        prompt_text = f"{system}\nCâu hỏi: {question}"
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
    )
    sql = (resp.text or "").strip()
    if sql and not sql.endswith(";"):
        sql += ";"
    return sql
    
def generate_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    # Có thể dùng feedback từ vòng trước
    feedback = state.get("feedback")
    sql = generate_sql_with_llm(question, feedback=feedback)
    return {**state, "sql": sql}


