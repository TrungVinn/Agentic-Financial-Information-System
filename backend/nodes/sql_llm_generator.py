from typing import Dict, Any, Optional
import os
import re
from google import generativeai as google_genai
from dotenv import load_dotenv

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

HINT_GUIDANCE = {
    "std_dev": "Tính độ lệch chuẩn bằng cách dùng STDDEV_POP(close) hoặc STDDEV_SAMP(close) trong PostgreSQL.",
    "moving_average": "Dùng window function (AVG(close) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)) để tính moving average theo số ngày yêu cầu.",
    "cumulative_return": "Dùng CTE để lấy giá mở đầu và kết thúc rồi tính (end_price - start_price) / start_price * 100 dưới tên percentage_return.",
    "days_count": "Đếm số phiên bằng COUNT(*) với điều kiện close lớn hơn/nhỏ hơn ngưỡng được nói trong câu hỏi.",
    "days_percentage": "Tính COUNT(*) thỏa điều kiện rồi chia cho tổng số ngày * 100 để ra phần trăm.",
    "ranking": "Sử dụng tổng lợi suất/return và ORDER BY DESC/ASC để xếp hạng; trả về TOP/LIMIT 3.",
    "max_drawdown": "Tính drawdown bằng cách so sánh mỗi giá với đỉnh trước đó (window MAX) rồi chọn drawdown tối đa.",
    "daily_return": "Tính daily return bằng LAG(close, 1) OVER (ORDER BY date) (KHÔNG dùng default value như LAG(close, 1, close)). Công thức: (close - LAG(close, 1)) / LAG(close, 1) * 100. Lưu ý: Filter ra các dòng NULL từ LAG hoặc dùng CASE WHEN để xử lý ngày đầu tiên.",
    "price_change": "Tính price change bằng LAG(close, 1) OVER (ORDER BY date) (KHÔNG dùng default value như LAG(close, 1, close)). Công thức: close - LAG(close, 1). Lưu ý: Filter ra các dòng NULL từ LAG hoặc dùng CASE WHEN để xử lý ngày đầu tiên.",
    "correlation": "Tính daily returns cho hai ticker bằng CTE với LAG(close, 1) (KHÔNG dùng default value), sau đó dùng công thức corr = (AVG(x*y) - AVG(x)*AVG(y)) / (STD_x * STD_y). Lưu ý: Filter ra các dòng NULL từ LAG.",
    "beta": "Tính daily returns bằng LAG(close, 1) (KHÔNG dùng default value) và dùng công thức beta = COV(stock, index) / VAR(index). Lưu ý: Filter ra các dòng NULL từ LAG.",
    "sharpe_ratio": "Tính daily returns bằng LAG(close, 1) (KHÔNG dùng default value), annualize trung bình và độ lệch chuẩn, rồi áp dụng (avg_return - risk_free_rate)/std_dev. Lưu ý: Filter ra các dòng NULL từ LAG.",
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


def generate_sql_with_llm(
    question: str, feedback: Optional[str] = None, analysis_hint: Optional[str] = None
) -> str:
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
        "SQL: SELECT p.ticker, c.name, AVG(p.close) AS avg_close FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE EXTRACT(YEAR FROM p.date) = 2024 GROUP BY p.ticker;\n\n"
        "Example 2: Total dividends per company in 2024\n"
        "Reasoning: We need total dividends for each company → GROUP BY ticker, use SUM(dividends).\n"
        "SQL: SELECT p.ticker, c.name, SUM(p.dividends) AS total_dividends FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE EXTRACT(YEAR FROM p.date) = 2024 GROUP BY p.ticker;\n\n"
        "Example 3: Scatter plot market cap vs P/E for all companies\n"
        "Reasoning: Each point = one company, no aggregation needed, just select from companies.\n"
        "SQL: SELECT symbol, name, market_cap, pe_ratio FROM companies;\n\n"
        "Example 4: Pie chart distribution by sector\n"
        "Reasoning: Each slice = one sector → GROUP BY sector, COUNT companies.\n"
        "SQL: SELECT sector, COUNT(*) AS count FROM companies GROUP BY sector;\n\n"
        "Example 5: Scatter plot average volume vs average price per company in 2024\n"
        "Reasoning: Each point = one company → GROUP BY ticker, aggregate AVG(volume) and AVG(close).\n"
        "SQL: SELECT p.ticker, c.name, AVG(p.volume) AS avg_volume, AVG(p.close) AS avg_close FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE EXTRACT(YEAR FROM p.date) = 2024 GROUP BY p.ticker;\n\n"
        "❌ SAI: GROUP BY date khi câu hỏi về 'per company'\n"
        "❌ SAI: Không GROUP BY khi cần aggregate per company\n"
        "❌ SAI: Include non-aggregated columns without GROUP BY\n\n"
    )

    system = (
        "Bạn là trợ lý tạo SQL cho PostgreSQL.\n\n"
        f"{schema}"
        f"{constraints}"
        f"{examples}"
        "=== QUY TẮC CHUNG ===\n"
        "- Trả về CHỈ SQL thuần túy, KHÔNG thêm markdown (```sql), giải thích hay comment.\n"
        "- Dùng tham số kiểu :ticker, :date, :year, :month, :quarter nếu phù hợp.\n"
        "- So sánh ngày: date = CAST(:date AS DATE) hoặc date::date = :date::date\n"
        "- Lọc theo năm: TO_CHAR(date, 'YYYY') = :year hoặc EXTRACT(YEAR FROM date) = :year\n"
        "- Lọc theo tháng: TO_CHAR(date, 'MM') = :month hoặc EXTRACT(MONTH FROM date) = :month\n"
        "- ⚠️ QUAN TRỌNG: KHÔNG BAO GIỜ dùng strftime() - đây là SQLite syntax, PostgreSQL KHÔNG hỗ trợ!\n"
        "- ⚠️ QUAN TRỌNG: KHÔNG dùng LIKE cho date, dùng TO_CHAR() hoặc EXTRACT().\n"
        "- JOIN: prices.ticker = companies.symbol\n"
        "- ⚠️ QUAN TRỌNG: Khi truy vấn thông tin từ bảng companies (sector, country, industry, description, website, market_cap, pe_ratio, dividend_yield, week_52_high, week_52_low, etc.),\n"
        "  NẾU đã biết ticker (có parameter :ticker), PHẢI LUÔN dùng WHERE companies.symbol = :ticker (KHÔNG BAO GIỜ dùng WHERE companies.name = :company hoặc WHERE companies.name ILIKE).\n"
        "  Ví dụ đúng: SELECT dividend_yield FROM companies WHERE symbol = :ticker;\n"
        "  Ví dụ đúng: SELECT week_52_high FROM companies WHERE symbol = :ticker;\n"
        "  Ví dụ sai: SELECT dividend_yield FROM companies WHERE name ILIKE '%' || :company || '%';\n"
        "  Ví dụ sai: SELECT week_52_high FROM companies WHERE name = 'Apple';\n"
        "- ⚠️ QUAN TRỌNG: Khi tìm ticker symbol theo tên công ty (ví dụ: 'What is the ticker symbol for Apple?'),\n"
        "  PHẢI dùng WHERE companies.name ILIKE '%' || :company || '%' (KHÔNG dùng WHERE companies.name = :company hoặc WHERE companies.name = 'Apple').\n"
        "  Lý do: Tên công ty trong database có thể là 'Apple Inc.' hoặc 'Apple, Inc.' chứ không phải chỉ 'Apple'.\n"
        "  → name = 'Apple' sẽ KHÔNG BAO GIỜ match được, kết quả luôn trả về 0 dòng!\n"
        "  Ví dụ đúng: SELECT symbol FROM companies WHERE name ILIKE '%' || :company || '%';\n"
        "  Ví dụ sai: SELECT symbol FROM companies WHERE name = 'Apple';\n"
        "- ⚠️ QUAN TRỌNG: Khi JOIN companies với prices và cần filter theo tên công ty:\n"
        "  * NẾU đã có parameter :ticker trong câu hỏi, PHẢI LUÔN dùng trực tiếp WHERE prices.ticker = :ticker hoặc WHERE companies.symbol = :ticker\n"
        "  * KHÔNG BAO GIỜ tạo CTE để tìm ticker từ tên công ty nếu đã có :ticker sẵn!\n"
        "  * CHỈ tạo CTE tìm ticker nếu câu hỏi KHÔNG có ticker và chỉ có tên công ty\n"
        "  * Nếu chỉ biết tên công ty (KHÔNG có :ticker): PHẢI dùng WHERE companies.name ILIKE '%' || :company || '%' (KHÔNG dùng WHERE companies.name = :company hoặc WHERE companies.name = 'literal')\n"
        "  Ví dụ đúng (có :ticker): SELECT ... FROM prices WHERE ticker = :ticker AND EXTRACT(YEAR FROM date) = :year;\n"
        "  Ví dụ SAI (có :ticker nhưng vẫn tạo CTE): WITH company_ticker AS (SELECT symbol FROM companies WHERE name ILIKE '%' || :company || '%') SELECT ... FROM prices p JOIN company_ticker ct ON p.ticker = ct.symbol;\n"
        "  Ví dụ đúng (chỉ có tên công ty, không có :ticker): SELECT ... FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE c.name ILIKE '%' || :company || '%';\n"
        "  Ví dụ sai: SELECT ... FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE c.name = 'Apple';\n"
        "- ⚠️ QUAN TRỌNG: Tên parameter phải đúng:\n"
        "  * Dùng :company (KHÔNG dùng :company_name)\n"
        "  * Dùng :ticker (KHÔNG dùng :ticker_symbol hoặc :symbol)\n"
        "  * Các parameter khác: :date, :year, :month, :quarter, :start_date, :end_date\n"
        "- Có thể dùng CTE, window functions, subqueries.\n"
        "- PostgreSQL có STDDEV_POP() và STDDEV_SAMP() cho độ lệch chuẩn.\n"
        "- Parameter binding: dùng :param (sẽ được convert sang %(param)s tự động).\n"
        "- ⚠️ QUAN TRỌNG: Khi dùng LAG() để tính daily return hoặc price change:\n"
        "  * KHÔNG BAO GIỜ dùng default value là chính giá trị hiện tại (ví dụ: LAG(close, 1, close))\n"
        "  * Lý do: Ngày đầu tiên sẽ có LAG = close, dẫn đến close - close = 0 (SAI)\n"
        "  * Giải pháp đúng: Dùng LAG(close, 1) (không có default) hoặc LAG(close, 1, NULL)\n"
        "  * Sau đó filter ra các dòng NULL: WHERE LAG(close, 1) IS NOT NULL\n"
        "  * Hoặc dùng CASE WHEN: CASE WHEN LAG(close, 1) IS NULL THEN NULL ELSE (close - LAG(close, 1)) / LAG(close, 1) * 100 END\n"
        "  * Ví dụ đúng: SELECT date, (close - LAG(close, 1) OVER (ORDER BY date)) / LAG(close, 1) OVER (ORDER BY date) * 100 AS daily_return FROM prices WHERE ticker = :ticker AND LAG(close, 1) OVER (ORDER BY date) IS NOT NULL\n\n"
        "=== QUY TRÌNH ===\n"
        "Bước 1: Mô tả ngắn gọn (1 câu) SQL phải tính toán gì và GROUP BY gì.\n"
        "Bước 2: Viết SQL.\n"
        'Format: "Reasoning: [mô tả]. SQL: [câu lệnh SQL]"\n'
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

    model = google_genai.GenerativeModel("gemini-2.5-flash")
    resp = model.generate_content(prompt_text)
    response_text = (resp.text or "").strip()

    # Extract SQL từ response (có thể có reasoning trước)
    sql = response_text
    # Nếu LLM trả về code block ở giữa text -> ưu tiên trích code block
    code_block_match = re.search(r"```[a-zA-Z0-9_-]*\n(.*?)```", sql, re.DOTALL)
    if code_block_match:
        sql = code_block_match.group(1).strip()
    if "SQL:" in response_text:
        sql = response_text.split("SQL:")[-1].strip()
    elif "sql:" in response_text.lower():
        sql = response_text.split("sql:")[-1].strip()

    sql = sql.strip()

    # Loại bỏ markdown code blocks nếu có
    # LLM đôi khi trả về: ```postgresql\nSELECT...\n``` hoặc ```sql\nSELECT...\n```
    if sql.startswith("```"):
        # Tìm dòng đầu tiên (```postgresql, ```sql, hoặc chỉ ```)
        lines = sql.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]  # Bỏ dòng đầu
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Bỏ dòng cuối
        sql = "\n".join(lines).strip()

    # Bỏ mọi phần text/Reasoning đứng trước câu lệnh SQL (chỉ giữ từ khóa SQL đầu tiên)
    first_sql_match = re.search(
        r"\b(WITH|SELECT|INSERT|UPDATE|DELETE)\b", sql, re.IGNORECASE
    )
    if first_sql_match:
        sql = sql[first_sql_match.start() :].strip()

    # Thêm dấu ; nếu chưa có
    if sql and not sql.endswith(";"):
        sql += ";"

    # Post-processing: Convert SQLite syntax sang PostgreSQL syntax
    # Chuyển strftime() thành EXTRACT() hoặc TO_CHAR()
    # Xử lý tất cả các pattern: strftime('%Y', date), strftime('%%Y', date), strftime('%%%Y', date), etc.
    # strftime('%Y', date) hoặc strftime('%%Y', date) -> EXTRACT(YEAR FROM date)
    sql = re.sub(
        r"strftime\s*\(\s*'%+Y'\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        r"EXTRACT(YEAR FROM \1)",
        sql,
        flags=re.IGNORECASE,
    )
    # strftime('%m', date) hoặc strftime('%%m', date) -> EXTRACT(MONTH FROM date)
    sql = re.sub(
        r"strftime\s*\(\s*'%+m'\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        r"EXTRACT(MONTH FROM \1)",
        sql,
        flags=re.IGNORECASE,
    )
    # strftime('%d', date) hoặc strftime('%%d', date) -> EXTRACT(DAY FROM date)
    sql = re.sub(
        r"strftime\s*\(\s*'%+d'\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        r"EXTRACT(DAY FROM \1)",
        sql,
        flags=re.IGNORECASE,
    )
    # strftime('%W', date) hoặc strftime('%%W', date) -> EXTRACT(WEEK FROM date)
    sql = re.sub(
        r"strftime\s*\(\s*'%+W'\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        r"EXTRACT(WEEK FROM \1)",
        sql,
        flags=re.IGNORECASE,
    )
    # strftime('%Y-%m-%d', date) hoặc strftime('%%Y-%%m-%%d', date) -> TO_CHAR(date, 'YYYY-MM-DD')
    sql = re.sub(
        r"strftime\s*\(\s*'%+Y-%+m-%+d'\s*,\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        r"TO_CHAR(\1, 'YYYY-MM-DD')",
        sql,
        flags=re.IGNORECASE,
    )
    # Xử lý trường hợp so sánh: strftime('%%Y', date) = '2024' -> EXTRACT(YEAR FROM date) = 2024
    # Loại bỏ dấu nháy đơn quanh số năm nếu có
    sql = re.sub(
        r"EXTRACT\(YEAR FROM ([a-zA-Z_][a-zA-Z0-9_.]*)\)\s*=\s*'(\d{4})'",
        r"EXTRACT(YEAR FROM \1) = \2",
        sql,
        flags=re.IGNORECASE,
    )
    # date('now', '-X month') -> CURRENT_DATE - INTERVAL 'X month'
    sql = re.sub(
        r"date\s*\(\s*'now'\s*,\s*'-(\d+)\s+month'\s*\)",
        r"CURRENT_DATE - INTERVAL '\1 month'",
        sql,
        flags=re.IGNORECASE,
    )
    # date('now', '-X day') -> CURRENT_DATE - INTERVAL 'X day'
    sql = re.sub(
        r"date\s*\(\s*'now'\s*,\s*'-(\d+)\s+day'\s*\)",
        r"CURRENT_DATE - INTERVAL '\1 day'",
        sql,
        flags=re.IGNORECASE,
    )

    # Post-processing: Sửa WHERE companies.name = 'literal' thành WHERE companies.name ILIKE '%literal%'
    # Áp dụng cho TẤT CẢ các trường hợp (không chỉ SELECT symbol)
    # Pattern: WHERE companies.name = '...' hoặc WHERE c.name = '...' hoặc WHERE name = '...' (trong context của companies)
    # Lý do: Tên công ty trong database là "Apple Inc." chứ không phải "Apple", nên name = 'Apple' sẽ không match
    
    # Sửa WHERE companies.name = 'literal' thành WHERE companies.name ILIKE '%literal%'
    sql = re.sub(
        r"WHERE\s+companies\.name\s*=\s*'([^']+)'",
        r"WHERE companies.name ILIKE '%' || '\1' || '%'",
        sql,
        flags=re.IGNORECASE,
    )
    # Sửa WHERE c.name = 'literal' thành WHERE c.name ILIKE '%literal%' (khi có alias c)
    sql = re.sub(
        r"WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\.name\s*=\s*'([^']+)'",
        lambda m: f"WHERE {m.group(1)}.name ILIKE '%' || '{m.group(2)}' || '%'" if m.group(1).lower() in ['c', 'companies', 'company'] else m.group(0),
        sql,
        flags=re.IGNORECASE,
    )
    # Sửa WHERE name = 'literal' khi đang query từ companies (SELECT ... FROM companies WHERE name = ...)
    if re.search(r"FROM\s+companies", sql, re.IGNORECASE) and not re.search(r"WHERE\s+companies\.name|WHERE\s+[a-zA-Z_]\.name", sql, re.IGNORECASE):
        sql = re.sub(
            r"WHERE\s+name\s*=\s*'([^']+)'",
            r"WHERE name ILIKE '%' || '\1' || '%'",
            sql,
            flags=re.IGNORECASE,
        )
    
    # Post-processing: Sửa WHERE name = '...' thành WHERE name ILIKE '%...%' khi tìm ticker symbol
    # Pattern: SELECT symbol FROM companies WHERE name = '...'
    # Hoặc: SELECT symbol FROM companies WHERE name = :company
    # Chỉ sửa khi đang SELECT symbol (ticker symbol query) - giữ lại logic cũ cho trường hợp đặc biệt
    if re.search(r"SELECT\s+symbol\s+FROM\s+companies", sql, re.IGNORECASE):
        # Sửa WHERE name = :company thành WHERE name ILIKE '%' || :company || '%'
        sql = re.sub(
            r"WHERE\s+name\s*=\s*:company\b",
            r"WHERE name ILIKE '%' || :company || '%'",
            sql,
            flags=re.IGNORECASE,
        )

    # Post-processing: Sửa WHERE name ILIKE '%' || :company || '%' thành WHERE symbol = :ticker
    # Khi đang query metadata từ companies (không phải ticker symbol query)
    # Chỉ sửa khi đang SELECT metadata fields (sector, country, industry, description, website, market_cap, pe_ratio, dividend_yield, week_52_high, week_52_low, etc.)
    metadata_fields_pattern = r"SELECT\s+(?:sector|country|industry|description|website|market_cap|pe_ratio|dividend_yield|week_52_high|week_52_low|52_week_high|52_week_low)\s+FROM\s+companies"
    if re.search(metadata_fields_pattern, sql, re.IGNORECASE) and not re.search(
        r"SELECT\s+symbol\s+FROM\s+companies", sql, re.IGNORECASE
    ):
        # Sửa WHERE name ILIKE '%' || :company || '%' thành WHERE symbol = :ticker
        sql = re.sub(
            r"WHERE\s+name\s+ILIKE\s+'%%'\s*\|\|\s*:company\s*\|\|\s*'%%'",
            r"WHERE symbol = :ticker",
            sql,
            flags=re.IGNORECASE,
        )
        # Sửa WHERE name = :company thành WHERE symbol = :ticker
        sql = re.sub(
            r"WHERE\s+name\s*=\s*:company\b",
            r"WHERE symbol = :ticker",
            sql,
            flags=re.IGNORECASE,
        )
        # Sửa WHERE name = 'literal' thành WHERE symbol = :ticker
        sql = re.sub(
            r"WHERE\s+name\s*=\s*'([^']+)'",
            r"WHERE symbol = :ticker",
            sql,
            flags=re.IGNORECASE,
        )

    # Post-processing: Sửa :company_name thành :company (tên parameter sai)
    sql = re.sub(
        r":company_name\b",
        r":company",
        sql,
        flags=re.IGNORECASE,
    )
    
    # Post-processing: Loại bỏ CTE tìm ticker nếu SQL đã có :ticker
    # Pattern: WITH company_ticker AS (SELECT symbol FROM companies WHERE name ILIKE ...) ... JOIN company_ticker
    # Nếu SQL có :ticker thì thay thế bằng WHERE ticker = :ticker trực tiếp
    if re.search(r":ticker\b", sql, re.IGNORECASE):
        # Tìm và loại bỏ CTE tìm ticker
        # Pattern: WITH company_ticker AS (SELECT symbol FROM companies WHERE name ILIKE '%' || :company || '%'), ... JOIN company_ticker ct ON ...
        cte_pattern = r"WITH\s+company_ticker\s+AS\s*\(\s*SELECT\s+symbol\s+FROM\s+companies\s+WHERE\s+name\s+ILIKE\s+'%%'\s*\|\|\s*:company\s*\|\|\s*'%%'\s*\)\s*,?\s*"
        if re.search(cte_pattern, sql, re.IGNORECASE):
            # Loại bỏ CTE
            sql = re.sub(cte_pattern, "", sql, flags=re.IGNORECASE)
            # Thay thế JOIN company_ticker ct ON p.ticker = ct.symbol thành WHERE p.ticker = :ticker
            sql = re.sub(
                r"JOIN\s+company_ticker\s+[a-zA-Z_]*\s+ON\s+[a-zA-Z_]*\.ticker\s*=\s*[a-zA-Z_]*\.symbol",
                "",
                sql,
                flags=re.IGNORECASE,
            )
            # Thêm WHERE ticker = :ticker nếu chưa có WHERE
            if not re.search(r"WHERE\s+.*ticker\s*=", sql, re.IGNORECASE):
                # Tìm vị trí sau FROM prices hoặc sau JOIN companies
                if re.search(r"FROM\s+prices", sql, re.IGNORECASE):
                    sql = re.sub(
                        r"(FROM\s+prices(?:\s+[a-zA-Z_]+)?)",
                        r"\1 WHERE ticker = :ticker",
                        sql,
                        flags=re.IGNORECASE,
                        count=1,
                    )
                elif re.search(r"JOIN\s+companies", sql, re.IGNORECASE):
                    # Nếu có JOIN companies, thêm WHERE sau JOIN
                    sql = re.sub(
                        r"(JOIN\s+companies(?:\s+[a-zA-Z_]+)?\s+ON\s+[^W]+)",
                        r"\1 WHERE prices.ticker = :ticker",
                        sql,
                        flags=re.IGNORECASE,
                        count=1,
                    )

    return sql


def generate_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    # Có thể dùng feedback từ vòng trước
    feedback = state.get("feedback")
    analysis_hint = state.get("analysis_hint")
    sql = generate_sql_with_llm(
        question, feedback=feedback, analysis_hint=analysis_hint
    )
    return {**state, "sql": sql, "used_sample": False}
