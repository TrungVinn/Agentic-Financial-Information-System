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
    
    # Dataset Schema
    schema = (
        "=== DATASET SCHEMA ===\n"
        "Table: prices\n"
        "  Columns: date (TEXT, format YYYY-MM-DD), open (REAL), high (REAL), low (REAL), close (REAL), "
        "volume (INTEGER), dividends (REAL), stock_splits (REAL), ticker (TEXT)\n"
        "  Note: prices.ticker joins with companies.symbol\n\n"
        "Table: companies\n"
        "  Columns: symbol (TEXT, primary key), name (TEXT), sector (TEXT), industry (TEXT), "
        "country (TEXT), website (TEXT), market_cap (REAL), pe_ratio (REAL), dividend_yield (REAL), "
        "week_52_high (REAL), week_52_low (REAL), description (TEXT)\n"
        "  Note: companies.symbol is the primary key, NOT 'ticker'\n\n"
    )
    
    # Constraints cho visualization queries
    constraints = (
        "=== QUY TẮC QUAN TRỌNG CHO VISUALIZATION ===\n"
        "1. Khi câu hỏi yêu cầu 'per company', 'each company', 'for each DJIA company':\n"
        "   → PHẢI GROUP BY ticker hoặc symbol (KHÔNG BAO GIỜ GROUP BY date)\n"
        "   → Mỗi dòng kết quả = một công ty\n\n"
        "2. Nếu câu hỏi liên quan đến toàn năm (in 2024, during 2024):\n"
        "   → Phải aggregate toàn bộ năm (AVG, SUM, COUNT cho cả năm)\n"
        "   → KHÔNG GROUP BY date (trừ khi user nói rõ 'per day')\n\n"
        "3. Scatter plot/correlation chart:\n"
        "   → Mỗi điểm = một company → GROUP BY ticker\n"
        "   → Trừ khi user nói 'per day' → GROUP BY date\n\n"
        "4. Bar chart:\n"
        "   → Một bar = một entity duy nhất (company hoặc day)\n"
        "   → Nếu 'per company' → GROUP BY ticker\n"
        "   → Nếu 'per day' → GROUP BY date\n\n"
        "5. Pie chart:\n"
        "   → Một slice = một category (sector, industry...)\n"
        "   → GROUP BY category đó (sector, industry...)\n\n"
        "6. Không được include columns không trong GROUP BY trừ khi chúng được aggregate (AVG, SUM, COUNT, MIN, MAX).\n\n"
    )
    
    # Few-shot examples
    examples = (
        "=== VÍ DỤ ĐÚNG (Few-shot Examples) ===\n\n"
        "Example 1: Average closing price per company in 2024\n"
        "Reasoning: We need one row per company → GROUP BY ticker, aggregate AVG(close) for the year.\n"
        "SQL: SELECT p.ticker, c.name, AVG(p.close) AS avg_close FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE strftime('%Y', p.date) = '2024' GROUP BY p.ticker;\n\n"
        "Example 2: Total dividends per company in 2024\n"
        "Reasoning: We need total dividends for each company → GROUP BY ticker, use SUM(dividends).\n"
        "SQL: SELECT p.ticker, c.name, SUM(p.dividends) AS total_dividends FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE strftime('%Y', p.date) = '2024' GROUP BY p.ticker;\n\n"
        "Example 3: Scatter plot market cap vs P/E for all companies\n"
        "Reasoning: Each point = one company, no aggregation needed, just select from companies.\n"
        "SQL: SELECT symbol, name, market_cap, pe_ratio FROM companies;\n\n"
        "Example 4: Pie chart distribution by sector\n"
        "Reasoning: Each slice = one sector → GROUP BY sector, COUNT companies.\n"
        "SQL: SELECT sector, COUNT(*) AS count FROM companies GROUP BY sector;\n\n"
        "Example 5: Scatter plot average volume vs average price per company in 2024\n"
        "Reasoning: Each point = one company → GROUP BY ticker, aggregate AVG(volume) and AVG(close).\n"
        "SQL: SELECT p.ticker, c.name, AVG(p.volume) AS avg_volume, AVG(p.close) AS avg_close FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE strftime('%Y', p.date) = '2024' GROUP BY p.ticker;\n\n"
        "❌ SAI: GROUP BY date khi câu hỏi về 'per company'\n"
        "❌ SAI: Không GROUP BY khi cần aggregate per company\n"
        "❌ SAI: Include non-aggregated columns without GROUP BY\n\n"
    )
    
    system = (
        "Bạn là trợ lý tạo SQL cho SQLite.\n\n"
        f"{schema}"
        f"{constraints}"
        f"{examples}"
        "=== QUY TẮC CHUNG ===\n"
        "- Trả về CHỈ SQL thuần túy, KHÔNG thêm markdown (```sql), giải thích hay comment.\n"
        "- Dùng tham số kiểu :ticker, :date, :year, :month, :quarter nếu phù hợp.\n"
        "- So sánh ngày: date(date) = date(:date) hoặc strftime('%Y-%m-%d', date) = :date\n"
        "- Lọc theo năm: strftime('%Y', date) = :year\n"
        "- Lọc theo tháng: strftime('%m', date) = :month\n"
        "- KHÔNG dùng LIKE cho date, dùng strftime() hoặc date().\n"
        "- JOIN: prices.ticker = companies.symbol\n"
        "- Có thể dùng CTE, window functions, subqueries.\n"
        "- SQLite không có STDDEV, dùng: SQRT(AVG(x*x) - AVG(x)*AVG(x)).\n\n"
        "=== QUY TRÌNH ===\n"
        "Bước 1: Mô tả ngắn gọn (1 câu) SQL phải tính toán gì và GROUP BY gì.\n"
        "Bước 2: Viết SQL.\n"
        "Format: \"Reasoning: [mô tả]. SQL: [câu lệnh SQL]\"\n"
    )
    
    hint_text = _build_hint_text(analysis_hint)
    if feedback:
        prompt_text = (
            f"{system}{hint_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Lỗi khi chạy SQL trước đó: {feedback}\n"
            f"Hãy sửa lại SQL theo đúng quy tắc trên."
        )
    else:
        prompt_text = f"{system}{hint_text}\n\nCâu hỏi: {question}"
    
    model = google_genai.GenerativeModel("gemini-2.0-flash")
    resp = model.generate_content(prompt_text)
    response_text = (resp.text or "").strip()
    
    # Extract SQL từ response (có thể có reasoning trước)
    sql = response_text
    if "SQL:" in response_text:
        sql = response_text.split("SQL:")[-1].strip()
    elif "sql:" in response_text.lower():
        sql = response_text.split("sql:")[-1].strip()
    
    sql = sql.strip()
    
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


