from typing import Dict, Any, Optional
import os
from google import generativeai as google_genai
from dotenv import load_dotenv

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

HINT_GUIDANCE = {
    "std_dev": "Tính độ lệch chuẩn bằng cách dùng SQRT(AVG(close * close) - AVG(close) * AVG(close)) trong SQLite.",
    "moving_average": "Dùng window function (AVG(close) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)) để tính moving average theo số ngày yêu cầu.",
    "cumulative_return": "Dùng CTE để lấy giá mở đầu và kết thúc rồi tính (end_price - start_price) / start_price * 100 dưới tên percentage_return.",
    "days_count": "Đếm số phiên bằng COUNT(*) với điều kiện close lớn hơn/nhỏ hơn ngưỡng được nói trong câu hỏi.",
    "days_percentage": "Tính COUNT(*) thỏa điều kiện rồi chia cho tổng số ngày * 100 để ra phần trăm.",
    "ranking": "Sử dụng tổng lợi suất/return và ORDER BY DESC/ASC để xếp hạng; trả về TOP/LIMIT 3.",
    "max_drawdown": "Tính drawdown bằng cách so sánh mỗi giá với đỉnh trước đó (window MAX) rồi chọn drawdown tối đa.",
    "correlation": "Tính daily returns cho hai ticker bằng CTE, sau đó dùng công thức corr = (AVG(x*y) - AVG(x)*AVG(y)) / (STD_x * STD_y).",
    "beta": "Tính daily returns và dùng công thức beta = COV(stock, index) / VAR(index).",
    "sharpe_ratio": "Tính daily returns, annualize trung bình và độ lệch chuẩn, rồi áp dụng (avg_return - risk_free_rate)/std_dev.",
    "single_day_drop": "Tính phần trăm thay đổi mỗi ngày ((close-open)/open*100) và chọn giá trị âm thấp nhất.",
    "single_day_gain": "Tương tự nhưng chọn giá trị cao nhất.",
}


def _build_hint_text(analysis_hint: Optional[str]) -> str:
    if not analysis_hint:
        return ""
    guidance = HINT_GUIDANCE.get(analysis_hint)
    if guidance:
        return f"\nYÊU CẦU NÂNG CAO: {guidance}"
    return f"\nYÊU CẦU NÂNG CAO: Hãy dùng CTE và các phép tính cần thiết để xử lý loại câu hỏi '{analysis_hint}'."


def generate_sql_with_llm(question: str, feedback: Optional[str] = None, analysis_hint: Optional[str] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    google_genai.configure(api_key=api_key)
    system = (
        "Bạn là trợ lý tạo SQL cho SQLite. Có 2 bảng:\n"
        "- prices(date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, dividends REAL, stock_splits REAL, ticker TEXT)\n"
        "  * Lưu ý: Bảng prices có cột 'ticker' (KHÔNG phải 'symbol')\n"
        "- companies(symbol TEXT, name TEXT, sector TEXT, industry TEXT, country TEXT, website TEXT, market_cap REAL, pe_ratio REAL, dividend_yield REAL, week_52_high REAL, week_52_low REAL, description TEXT)\n"
        "  * Lưu ý: Bảng companies có cột 'symbol'\n\n"
        "Quy tắc bắt buộc:\n"
        "- Trả về CHỈ SQL thuần túy, KHÔNG thêm markdown (```sql), giải thích hay comment.\n"
        "- Dùng tham số kiểu :ticker, :date, :year, :month, :quarter nếu phù hợp.\n"
        "- So sánh ngày cụ thể: date(date) = date(:date) HOẶC date = :date\n"
        "- Lọc theo năm: strftime('%Y', date) = :year\n"
        "- Lọc theo tháng: strftime('%m', date) = :month\n"
        "- KHÔNG dùng LIKE cho date, dùng strftime() hoặc date().\n"
        "- Bảng prices JOIN với companies: JOIN companies ON prices.ticker = companies.symbol\n"
        "- Có thể dùng CTE, window functions, subqueries.\n"
        "- SQLite không có STDDEV, dùng: SQRT(AVG(x*x) - AVG(x)*AVG(x)).\n"
    )
    hint_text = _build_hint_text(analysis_hint)
    if feedback:
        prompt_text = (
            f"{system}{hint_text}\nCâu hỏi: {question}\n\nLỗi khi chạy SQL trước đó, hãy sửa câu lệnh: {feedback}"
        )
    else:
        prompt_text = f"{system}{hint_text}\nCâu hỏi: {question}"
    
    model = google_genai.GenerativeModel("gemini-2.0-flash")
    resp = model.generate_content(prompt_text)
    sql = (resp.text or "").strip()
    
    # Loại bỏ markdown code blocks nếu có
    # LLM đôi khi trả về: ```sqlite\nSELECT...\n``` hoặc ```sql\nSELECT...\n```
    if sql.startswith("```"):
        # Tìm dòng đầu tiên (```sqlite, ```sql, hoặc chỉ ```)
        lines = sql.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]  # Bỏ dòng đầu
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Bỏ dòng cuối
        sql = "\n".join(lines).strip()
    
    # Thêm dấu ; nếu chưa có
    if sql and not sql.endswith(";"):
        sql += ";"
    
    return sql
    
def generate_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    # Có thể dùng feedback từ vòng trước
    feedback = state.get("feedback")
    analysis_hint = state.get("analysis_hint")
    sql = generate_sql_with_llm(question, feedback=feedback, analysis_hint=analysis_hint)
    return {**state, "sql": sql, "used_sample": False}


