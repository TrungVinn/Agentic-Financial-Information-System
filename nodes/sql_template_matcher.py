from typing import Dict, Any, Optional, Tuple, List
import re
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from config import DB_PATH, SQL_SAMPLES_FILE, DJIA_COMPANIES_CSV
from nodes.utils import normalize_text, extract_date_parts, extract_date_range, extract_ticker

def build_chart_sql(chart_request: Optional[Dict[str, Any]]) -> str:
    if chart_request and chart_request.get("start_date") and chart_request.get("end_date"):
        return """
SELECT date, open, high, low, close, volume
FROM prices
WHERE ticker = :ticker
  AND date(date) BETWEEN date(:start_date) AND date(:end_date)
ORDER BY date ASC;
""".strip()
    return """
WITH recent AS (
    SELECT date, open, high, low, close, volume
    FROM prices
    WHERE ticker = :ticker
    ORDER BY date DESC
    LIMIT :window_days
)
SELECT * FROM recent
ORDER BY date ASC;
""".strip()

# Load environment variables
load_dotenv()

# Setup Gemini API key
if os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

def detect_two_tickers(question: str) -> Tuple[Optional[str], Optional[str]]:
    """Cố gắng phát hiện 2 công ty trong câu hỏi (dựa vào alias/ticker)."""
    q = normalize_text(question)
    
    # Pattern 1: "which had a higher closing price: A or B?"
    colon_or_match = re.search(r":\s*([^:]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if colon_or_match:
        company1 = colon_or_match.group(1).strip()
        company2 = colon_or_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 2: "which company had a higher closing price, A or B?"
    comma_or_match = re.search(r",\s*([^,]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if comma_or_match:
        company1 = comma_or_match.group(1).strip()
        company2 = comma_or_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 3: "which company's stock closed higher: A or B?"
    apostrophe_match = re.search(r"stock\s+(?:closed\s+)?higher[^:]*:\s*([^,]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if apostrophe_match:
        company1 = apostrophe_match.group(1).strip()
        company2 = apostrophe_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 4: "who closed higher: A or B?"
    who_match = re.search(r"who\s+(?:closed\s+)?higher[^:]*:\s*([^,]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if who_match:
        company1 = who_match.group(1).strip()
        company2 = who_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 5: "which stock was higher, A or B?"
    stock_was_match = re.search(r"stock\s+was\s+higher[^,]*,\s*([^,]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if stock_was_match:
        company1 = stock_was_match.group(1).strip()
        company2 = stock_was_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 6: "which had a higher closing price, A or B?"
    which_had_match = re.search(r"which\s+had\s+a\s+higher[^,]*,\s*([^,]+?)\s+or\s+([^?]+)", q, re.IGNORECASE)
    if which_had_match:
        company1 = which_had_match.group(1).strip()
        company2 = which_had_match.group(2).strip()
        t1 = extract_ticker(company1)
        t2 = extract_ticker(company2)
        if t1 and t2:
            return t1, t2
    
    # Pattern 7: tách theo ' vs ', ' versus ', ' or '
    parts = re.split(r"\bvs\b|\bversus\b|\bor\b", q)
    if len(parts) >= 2:
        t1 = extract_ticker(parts[0])
        t2 = extract_ticker(parts[1])
        if t1 and t2:
            return t1, t2
    
    # Pattern 8: fallback - tìm tất cả tickers xuất hiện
    tickers = re.findall(r"\b([A-Z]{2,5})\b", question)
    if len(tickers) >= 2:
        return tickers[0], tickers[1]
    return None, None

def load_sql_samples() -> List[str]:
    """Load SQL samples từ file."""
    if not SQL_SAMPLES_FILE.exists():
        return []
    
    text = SQL_SAMPLES_FILE.read_text(encoding="utf-8")
    statements = [s.strip() + ";" for s in re.split(r";\s*\n", text) if s.strip()]
    
    return statements

def validate_and_find_sql_with_llm(question: str, heuristic_sql: Optional[str], sql_samples: List[str]) -> Optional[str]:
    """Sử dụng LLM để validate heuristic SQL. Nếu không phù hợp, trả về None để gọi sql_llm_generator."""
    if not sql_samples:
        return heuristic_sql
    
    # Tạo prompt cho LLM validation
    samples_text = "\n".join([f"{i+1}. {sql}" for i, sql in enumerate(sql_samples[:20])])  # Giới hạn 20 samples
    
    if heuristic_sql is None:
        # Trường hợp heuristic không tìm được SQL, LLM tìm trong danh sách với độ chính xác cao
        prompt = f"""
Bạn là một chuyên gia SQL và phân tích câu hỏi. Heuristic rules không tìm được SQL mẫu phù hợp. Hãy tìm SQL mẫu phù hợp CHÍNH XÁC với câu hỏi từ danh sách dưới đây.

CÂU HỎI: {question}

DANH SÁCH SQL MẪU CÓ SẴN:
{samples_text}

NHIỆM VỤ:
Phân tích câu hỏi và tìm SQL mẫu phù hợp CHÍNH XÁC từ danh sách trên.

QUY TẮC CHÍNH XÁC:
- Câu hỏi về dividend yield cần SQL tính toán từ dividends và close price
- Câu hỏi so sánh 2 công ty cần SQL có a_ và b_ hoặc CROSS JOIN
- Câu hỏi về 1 công ty cần SQL đơn giản với WHERE ticker = :ticker  
- Câu hỏi theo ngày cần date(:date), theo năm cần strftime('%Y', date) = :year
- Parameters phải phù hợp CHÍNH XÁC với câu hỏi (:ticker, :date, :year, :ticker_a, :ticker_b, etc.)

QUAN TRỌNG: Chỉ chọn SQL mẫu nếu nó phù hợp CHÍNH XÁC với câu hỏi. Nếu không chắc chắn 100%, hãy trả về NO_MATCH.

TRẢ LỜI:
- "FOUND: [số]" nếu tìm thấy SQL phù hợp CHÍNH XÁC (ví dụ: FOUND: 5)
- "NO_MATCH" nếu không tìm thấy SQL phù hợp CHÍNH XÁC nào

CHỈ TRẢ LỜI: FOUND: [số] hoặc NO_MATCH"""
    else:
        # Trường hợp heuristic tìm được SQL, LLM validate với độ chính xác cao
        prompt = f"""
Bạn là một chuyên gia SQL và phân tích câu hỏi. Tôi có một câu hỏi và một SQL mẫu được tìm bởi heuristic rules.

CÂU HỎI: {question}

SQL MẪU ĐƯỢC TÌM BỞI HEURISTIC: 
{heuristic_sql}

DANH SÁCH SQL MẪU CÓ SẴN:
{samples_text}

NHIỆM VỤ:
1. Phân tích câu hỏi để hiểu yêu cầu
2. Kiểm tra xem SQL mẫu heuristic có phù hợp CHÍNH XÁC với câu hỏi không
3. Nếu SQL heuristic KHÔNG phù hợp, hãy tìm SQL mẫu phù hợp CHÍNH XÁC từ danh sách trên

QUY TẮC KIỂM TRA CHÍNH XÁC:
- Câu hỏi về dividend yield cần SQL tính toán từ dividends và close price
- Câu hỏi so sánh 2 công ty cần SQL có a_ và b_ hoặc CROSS JOIN
- Câu hỏi về 1 công ty cần SQL đơn giản với WHERE ticker = :ticker  
- Câu hỏi theo ngày cần date(:date), theo năm cần strftime('%Y', date) = :year
- Parameters phải phù hợp CHÍNH XÁC với câu hỏi (:ticker, :date, :year, :ticker_a, :ticker_b, etc.)

QUAN TRỌNG: Chỉ chọn SQL mẫu nếu nó phù hợp CHÍNH XÁC với câu hỏi. Nếu không chắc chắn 100%, hãy trả về NO_MATCH.

TRẢ LỜI:
- "HEURISTIC_OK" nếu SQL heuristic phù hợp CHÍNH XÁC với câu hỏi
- "FOUND_BETTER: [số]" nếu tìm thấy SQL tốt hơn và CHÍNH XÁC hơn (ví dụ: FOUND_BETTER: 5)
- "NO_MATCH" nếu không tìm thấy SQL phù hợp CHÍNH XÁC nào

CHỈ TRẢ LỜI: HEURISTIC_OK hoặc FOUND_BETTER: [số] hoặc NO_MATCH"""

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            max_tokens=100
        )
        
        response = llm.invoke(prompt)
        result = response.content.strip()
        
        # Parse kết quả
        if heuristic_sql is None:
            # Trường hợp heuristic không tìm được SQL
            if result.startswith("FOUND:"):
                # Trích xuất số từ "FOUND: 5"
                try:
                    idx_str = result.split(":")[1].strip()
                    idx = int(idx_str) - 1  # Convert to 0-based index
                    if 0 <= idx < len(sql_samples):
                        return sql_samples[idx]
                except (ValueError, IndexError):
                    pass
            elif result == "NO_MATCH":
                return None  # Trả về None để trigger sql_llm_generator
            # Fallback về None nếu parse lỗi
            return None
        else:
            # Trường hợp heuristic tìm được SQL
            if result == "HEURISTIC_OK":
                return heuristic_sql
            elif result.startswith("FOUND_BETTER:"):
                # Trích xuất số từ "FOUND_BETTER: 5"
                try:
                    idx_str = result.split(":")[1].strip()
                    idx = int(idx_str) - 1  # Convert to 0-based index
                    if 0 <= idx < len(sql_samples):
                        return sql_samples[idx]
                except (ValueError, IndexError):
                    pass
                # Fallback về heuristic nếu parse lỗi
                return heuristic_sql
            elif result == "NO_MATCH":
                return None  # Trả về None để trigger sql_llm_generator
            # Fallback về heuristic nếu LLM không trả về kết quả hợp lệ
            return heuristic_sql
        
    except Exception as e:
        print(f"LLM validation error: {e}")
        return heuristic_sql

def match_sample(question: str) -> Optional[str]:
    """Sử dụng heuristic rules để tìm SQL sample tốt nhất, sau đó validate bằng LLM."""
    q = normalize_text(question)
    sql_samples = load_sql_samples()

    def find_sample_with(markers: List[str]) -> Optional[str]:
        for s in sql_samples:
            text = s.lower()
            if all(m.lower() in text for m in markers):
                return s
        return None

    parts = extract_date_parts(question)
    has_date = "date" in parts
    has_year = "year" in parts
    start_date, end_date = extract_date_range(question)
    has_date_range = start_date is not None and end_date is not None
    ticker = extract_ticker(question)
    t1, t2 = detect_two_tickers(question)

    # Tìm SQL bằng heuristic rules - SẮP XẾP THEO THỨ TỰ TYPE VÀ COMPLEXITY NHƯ SQL_SAMPLES
    heuristic_sql = None

    # ===== FACTUAL, EASY =====
    # 1) Factual, easy theo ngày - CHỈ KHI KHÔNG PHẢI COMPARATIVE
    if not heuristic_sql and not ("which company" in q or "công ty nào" in q):
        if ("closing price" in q or "giá đóng cửa" in q) and has_date and not has_date_range and not (t1 and t2) and ("change" not in q and "from" not in q and "to" not in q):
            s = find_sample_with(["select close", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("opening price" in q or "giá mở cửa" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select open", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("highest price" in q or "giá cao nhất" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select high", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("lowest price" in q or "giá thấp nhất" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select low", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("trading volume" in q or "khối lượng" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select volume", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("dividend" in q or "cổ tức" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select dividends", "date(:date)"])
            if s:
                heuristic_sql = s
        if ("stock split" in q or "chia tách" in q or "tách cổ phiếu" in q) and has_date and not has_date_range and not (t1 and t2):
            s = find_sample_with(["select stock_splits", "date(:date)"])
            if s:
                heuristic_sql = s

    # ===== FACTUAL, MEDIUM =====
    # 2) Factual, medium theo năm - CHỈ KHI KHÔNG PHẢI COMPARATIVE
    if not heuristic_sql and not ("which company" in q or "công ty nào" in q):
        # Highest closing price in {year}
        if ("highest closing price" in q or ("cao nhất" in q and "đóng cửa" in q)) and has_year and not has_date:
            s = find_sample_with(["order by close desc", "strftime('%Y', date) = :year"])
            if s:
                heuristic_sql = s
        # Lowest closing price in {year}
        if ("lowest closing price" in q or ("thấp nhất" in q and "đóng cửa" in q)) and has_year and not has_date:
            s = find_sample_with(["order by close asc", "strftime('%Y', date) = :year"])
            if s:
                heuristic_sql = s
        # How many dividends in {year}
        if ("how many dividends" in q or "bao nhiêu lần cổ tức" in q or ("dividends" in q and "in" in q and has_year)) and has_year:
            s = find_sample_with(["count(*) as dividends_count", "dividends > 0"])
            if s:
                heuristic_sql = s
        # Dividend per share on {date}
        if ("dividend per share" in q or ("cổ tức" in q and ("ngày" in q or "vào" in q))) and has_date:
            s = find_sample_with(["select dividends as dividend_per_share", "date(:date)"])
            if s:
                heuristic_sql = s
        # Stock split date and ratio
        if ("stock split" in q or "chia tách" in q or "tách cổ phiếu" in q):
            s = find_sample_with(["split_ratio", "stock splits"])
            if s:
                heuristic_sql = s
        # Highest opening price in {year}
        if not heuristic_sql and ("opening price" in q or "giá mở cửa" in q or "gia mo cua" in q) and has_year and not has_date:
            if "highest" in q or "cao" in q:
                s = find_sample_with(["open AS max_open", "order by open desc"])
                if s:
                    heuristic_sql = s
            if not heuristic_sql and ("lowest" in q or "thấp" in q or "thap" in q):
                s = find_sample_with(["open AS min_open", "order by open asc"])
                if s:
                    heuristic_sql = s

    # ===== COMPARATIVE, EASY =====
    # 3) Comparative (2 công ty) với date
    if not heuristic_sql and (t1 and t2) and has_date and not has_date_range:
        # Kiểm tra các pattern cụ thể từ djia_qna.json
        comparative_patterns = [
            "which company had a higher",
            "which had a higher", 
            "which company's stock closed higher",
            "who closed higher",
            "which stock was higher",
            "which company's stock price was higher"
        ]
        
        is_comparative_pattern = any(pattern in q for pattern in comparative_patterns)
        
        if is_comparative_pattern:
            # Tìm comparative template phù hợp theo field
            if ("closing price" in q or "closed" in q):
                s = find_sample_with(["a_close", "b_close", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("opening price" in q):
                s = find_sample_with(["a_open", "b_open", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("high" in q):
                s = find_sample_with(["a_high", "b_high", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("low" in q):
                s = find_sample_with(["a_low", "b_low", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("volume" in q):
                s = find_sample_with(["a_volume", "b_volume", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("dividend" in q):
                s = find_sample_with(["a_dividends", "b_dividends", "date(:date)"])
                if s:
                    heuristic_sql = s
            elif ("stock split" in q):
                s = find_sample_with(["a_stock_splits", "b_stock_splits", "date(:date)"])
                if s:
                    heuristic_sql = s

    # 4) Comparative (2 công ty) với year (dividend questions)
    if not heuristic_sql and (t1 and t2) and has_year and ("dividend" in q or "dividends" in q or "cổ tức" in q) and ("higher" in q or "cao hơn" in q or "which" in q or "ai" in q):
        s = find_sample_with(["a_dividends_per_share", "b_dividends_per_share"])
        if s:
            heuristic_sql = s

    # ===== COMPARATIVE, MEDIUM =====
    # 5) Comparative, medium: "Which company had the highest/lowest <field> on {date}?"
    if not heuristic_sql and has_date and not has_date_range and not (t1 and t2) and ("which company" in q or "công ty nào" in q):
        # Close - highest
        if ("closing price" in q or "đóng cửa" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, close", "order by p.close desc"])
            if s:
                heuristic_sql = s
        # Close - lowest
        if ("closing price" in q or "đóng cửa" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, close", "order by p.close asc"])
            if s:
                heuristic_sql = s
        # Open - highest
        if ("opening price" in q or "giá mở" in q or "giá mở cửa" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, open", "order by p.open desc"])
            if s:
                heuristic_sql = s
        # Open - lowest
        if ("opening price" in q or "giá mở" in q or "giá mở cửa" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, open", "order by p.open asc"])
            if s:
                heuristic_sql = s
        # Intraday High - highest (chỉ khi có "intraday" rõ ràng)
        if ("intraday high" in q or "giá cao nhất trong ngày" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, high", "order by p.high desc"])
            if s:
                heuristic_sql = s
        # Intraday High - lowest
        if ("intraday high" in q or "giá cao nhất trong ngày" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, high", "order by p.high asc"])
            if s:
                heuristic_sql = s
        # Intraday Low - highest (chỉ khi có "intraday" rõ ràng)
        if ("intraday low" in q or "giá thấp nhất trong ngày" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, low", "order by p.low desc"])
            if s:
                heuristic_sql = s
        # Intraday Low - lowest
        if ("intraday low" in q or "giá thấp nhất trong ngày" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, low", "order by p.low asc"])
            if s:
                heuristic_sql = s
        # Volume - highest
        if ("volume" in q or "khối lượng" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, volume", "order by p.volume desc"])
            if s:
                heuristic_sql = s
        # Volume - lowest
        if ("volume" in q or "khối lượng" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, volume", "order by p.volume asc"])
            if s:
                heuristic_sql = s
        # Dividends - highest
        if ("dividend" in q or "cổ tức" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, dividends", "order by p.dividends desc"])
            if s:
                heuristic_sql = s
        # Dividends - lowest
        if ("dividend" in q or "cổ tức" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, dividends", "order by p.dividends asc"])
            if s:
                heuristic_sql = s
        # Stock splits - highest
        if ("stock split" in q or "split ratio" in q or "chia tách" in q or "tách cổ phiếu" in q) and ("highest" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, stock_splits", "order by p.stock_splits desc"])
            if s:
                heuristic_sql = s
        # Stock splits - lowest
        if ("stock split" in q or "split ratio" in q or "chia tách" in q or "tách cổ phiếu" in q) and ("lowest" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, stock_splits", "order by p.stock_splits asc"])
            if s:
                heuristic_sql = s

    # ===== COMPARATIVE, DIFFICULT =====
    # 6) Comparative, difficult: percentage/absolute changes over time periods
    if not heuristic_sql and has_year and not has_date and not (t1 and t2):
        # Largest percentage increase in {year}
        if ("largest percentage increase" in q or "tỷ lệ tăng" in q) and ("stock price" in q or "cổ phiếu" in q):
            s = find_sample_with(["percentage_change", "with daily_closes", "row_number() over (partition by ticker order by date asc)"])
            if s:
                heuristic_sql = s
        # Largest absolute increase in {year}
        if ("largest absolute increase" in q or "mức tăng tuyệt đối" in q) and ("dollars" in q or "usd" in q):
            s = find_sample_with(["absolute_change", "with daily_closes", "last_close - first_close"])
            if s:
                heuristic_sql = s
        # Largest percentage decline in {year}
        if ("largest percentage decline" in q or "tỷ lệ giảm" in q) and ("stock price" in q or "cổ phiếu" in q):
            s = find_sample_with(["percentage_decline", "with price_changes", "min(close) - max(close)"])
            if s:
                heuristic_sql = s

    # 7) Price change between two specific dates
    if not heuristic_sql and ("change from" in q or "thay đổi từ" in q or ("from" in q and "to" in q)):
        s = find_sample_with(["price_change", "start_price", "end_price", "cross join"])
        if s:
            heuristic_sql = s

    # ===== ANALYTICAL, EASY =====
    # 8) Analytical, easy: averages, quarters, half-year
    if not heuristic_sql and has_year and ticker is not None:
        # Average closing price from month X to month Y (ƯU TIÊN TRƯỚC)
        if ("average closing price" in q or "trung bình" in q) and ("from" in q or "through" in q or "đến" in q or "den" in q or "-" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) between :start_month and :end_month"])
            if s:
                heuristic_sql = s
        # Average closing price in month (CHỈ KHI KHÔNG CÓ FROM/THROUGH)
        if not heuristic_sql and ("average closing price" in q or "trung bình" in q) and ("march" in q or "april" in q or "may" in q or "june" in q or "july" in q or "august" in q or "september" in q or "october" in q or "november" in q or "december" in q or "january" in q or "february" in q) and not ("from" in q or "through" in q or "đến" in q or "den" in q or "-" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) = :month"])
            if s:
                heuristic_sql = s
        # Average closing price in quarter
        if ("average closing price" in q or "trung bình" in q) and ("q1" in q or "q2" in q or "q3" in q or "q4" in q or "quarter" in q or "quý" in q or "first quarter" in q):
            s = find_sample_with(["avg_close", ":quarter"])
            if s:
                heuristic_sql = s
        # Average daily trading volume
        if ("average daily trading volume" in q or "khối lượng trung bình" in q):
            s = find_sample_with(["avg_volume", "avg(volume)"])
            if s:
                heuristic_sql = s
        # Percentage increase in year
        if ("percentage" in q or "phần trăm" in q) and ("increase" in q or "tăng" in q):
            s = find_sample_with(["percentage_increase", "with year_prices"])
            if s:
                heuristic_sql = s
        # Second half average
        if ("second half" in q or "nửa cuối" in q) and ("average" in q or "trung bình" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) in ('07', '08', '09', '10', '11', '12')"])
            if s:
                heuristic_sql = s

    # ===== ANALYTICAL, MEDIUM =====
    # 9) Analytical, medium: totals, month ranges
    if not heuristic_sql and has_year and ticker is not None:
        # Total trading volume in year
        if ("total trading volume" in q or ("tổng" in q and "khối lượng" in q)):
            s = find_sample_with(["sum(volume) as total_volume", "strftime('%Y', date) = :year"])
            if s:
                heuristic_sql = s

    # ===== FACTUAL, EASY (COMPANIES METADATA) =====
    # 10) Company metadata factual easy: sector and ticker symbol
    if not heuristic_sql and ticker is not None:
        # Sector of company
        if ("which sector" in q or "sector" in q or "thuộc ngành" in q):
            s = find_sample_with(["select sector", "from companies"])
            if s:
                heuristic_sql = s
        # Ticker symbol of company
        if ("ticker symbol" in q or "mã cổ phiếu" in q or "mã" in q):
            s = find_sample_with(["fields: symbol"])
            if s:
                heuristic_sql = s

    # ===== COMPARATIVE, EASY (YEARLY) =====
    # 11) Comparative (2 công ty) với year (stock split questions)
    if not heuristic_sql and (t1 and t2) and has_year and ("stock split" in q or "chia tách" in q or "tách cổ phiếu" in q):
        s = find_sample_with(["a_stock_splits", "b_stock_splits", "date(:date)"])
        if s:
            heuristic_sql = s

    # ===== ANALYTICAL, MEDIUM (INDEX-LEVEL) =====
    # 12) Index-level: average dividend yield for DJIA as a whole
    if not heuristic_sql and ("dividend yield" in q or "lợi suất cổ tức" in q) and ("djia" in q or "as a whole" in q or "toàn bộ" in q or "toan bo" in q):
        s = find_sample_with(["avg_dividend_yield", "from companies"])
        if s:
            heuristic_sql = s

    # ===== OTHER ANALYTICAL PATTERNS =====
    # 13) Other analytical patterns
    if not heuristic_sql:
        key_map = [
            ("median", "median_close"),
            ("trung vị", "median_close"),
        ]
        for key, signature in key_map:
            if key in q:
                for s in sql_samples:
                    if signature.lower() in s.lower():
                        heuristic_sql = s
                        break
                if heuristic_sql:
                    break

    # Sử dụng LLM để validate và tìm SQL phù hợp
    return validate_and_find_sql_with_llm(question, heuristic_sql, sql_samples)

def match_sql_template(state: Dict[str, Any]) -> Dict[str, Any]:
    """Trích xuất ticker và tìm SQL template phù hợp với câu hỏi."""
    question = state.get("question", "")
    needs_chart = state.get("needs_chart", False)
    chart_request = state.get("chart_request")
    
    # Trích xuất ticker (gộp logic từ alias_resolver)
    ticker = extract_ticker(question)
    
    if needs_chart:
        sql = build_chart_sql(chart_request)
        return {**state, "ticker": ticker, "sql": sql, "used_sample": True}
    
    if state.get("force_llm"):
        return {**state, "ticker": ticker, "sql": None, "used_sample": False}
    
    # Tìm SQL template
    sql = match_sample(question)
    used_sample = sql is not None
    
    return {**state, "ticker": ticker, "sql": sql, "used_sample": used_sample}


