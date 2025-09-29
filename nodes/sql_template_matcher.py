from typing import Dict, Any, Optional, Tuple, List
import re
from config import DB_PATH, SQL_SAMPLES_FILE, DJIA_COMPANIES_CSV
from nodes.utils import normalize_text, extract_date_parts, extract_date_range, extract_ticker

def detect_two_tickers(question: str) -> Tuple[Optional[str], Optional[str]]:
    """Cố gắng phát hiện 2 công ty trong câu hỏi (dựa vào alias/ticker)."""
    q = normalize_text(question)
    # tách theo ' vs ', ' versus ', ' or '
    parts = re.split(r"\bvs\b|\bversus\b|\bor\b", q)
    if len(parts) >= 2:
        t1 = extract_ticker(parts[0])
        t2 = extract_ticker(parts[1])
        return t1, t2
    # fallback: tìm tất cả tickers xuất hiện
    tickers = re.findall(r"\b([A-Z]{2,5})\b", question)
    if len(tickers) >= 2:
        return tickers[0], tickers[1]
    return None, None

def load_sql_samples() -> List[str]:
    if not SQL_SAMPLES_FILE.exists():
        return []
    text = SQL_SAMPLES_FILE.read_text(encoding="utf-8")
    # Cắt theo dấu ; ở cuối câu lệnh
    statements = [s.strip() + ";" for s in re.split(r";\s*\n", text) if s.strip()]
    return statements

def match_sample(question: str) -> Optional[str]:
    q = normalize_text(question)
    samples = load_sql_samples()

    def find_sample_with(markers: List[str]) -> Optional[str]:
        for s in samples:
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

    # 0) Comparative (2 công ty) - ưu tiên các câu theo NĂM (không yêu cầu :date) để tránh nhầm sang mẫu theo ngày
    if (t1 and t2) and has_year and ("dividend" in q or "dividends" in q or "cổ tức" in q) and ("higher" in q or "cao hơn" in q or "which" in q or "ai" in q):
        s = find_sample_with(["a_dividends_per_share", "b_dividends_per_share"]) or find_sample_with(["sum(dividends)", "strftime('%Y', date) = :year"]) 
        if s:
            return s

    # 0bis) Comparative (2 công ty) ưu tiên bắt trước để tránh nhầm sang easy
    if (t1 and t2) and ("higher" in q or "cao hơn" in q or "which" in q or "ai" in q):
        # Ưu tiên theo field được nhắc đến
        if ("closing price" in q or "giá đóng" in q):
            s = find_sample_with(["a_close", "b_close", "date(:date)"])
            if s:
                return s
        if ("opening price" in q or "giá mở" in q or "giá mở cửa" in q):
            s = find_sample_with(["a_open", "b_open", "date(:date)"])
            if s:
                return s
        if ("high" in q or "cao nhất" in q):
            s = find_sample_with(["a_high", "b_high", "date(:date)"])
            if s:
                return s
        if ("low" in q or "thấp nhất" in q):
            s = find_sample_with(["a_low", "b_low", "date(:date)"])
            if s:
                return s
        if ("volume" in q or "khối lượng" in q):
            s = find_sample_with(["a_volume", "b_volume", "date(:date)"])
            if s:
                return s
        if ("dividend" in q or "dividends" in q or "cổ tức" in q):
            s = find_sample_with(["a_dividends", "b_dividends", "date(:date)"])
            if s:
                return s
    # Comparative, easy: yearly dividends per share higher (company A vs B)
    if (t1 and t2) and has_year and ("dividend" in q or "dividends" in q or "cổ tức" in q) and ("higher" in q or "cao hơn" in q or "which" in q or "ai" in q):
        s = find_sample_with(["dividends_per_share", "sum(dividends)"]) or find_sample_with(["a_dividends_per_share", "b_dividends_per_share"]) or find_sample_with(["strftime('%Y', date) = :year"]) 
        if s:
            return s
        if ("stock split" in q or "chia tách" in q or "tách cổ phiếu" in q):
            s = find_sample_with(["a_stock_splits", "b_stock_splits", "date(:date)"])
            if s:
                return s

    # A) Comparative, medium: "Which company had the highest/lowest <field> on {date}?"
    if has_date and not has_date_range and not (t1 and t2) and ("which company" in q or "công ty nào" in q):
        # Close
        if ("closing price" in q or "đóng cửa" in q):
            s = find_sample_with(["fields: company, close", "order by p.close desc"]) or find_sample_with(["fields: company, close", "order by p.close asc"])
            if s:
                return s
        # Open
        if ("opening price" in q or "giá mở" in q or "giá mở cửa" in q):
            s = find_sample_with(["fields: company, open", "order by p.open desc"]) or find_sample_with(["fields: company, open", "order by p.open asc"])
            if s:
                return s
        # High
        if ("high" in q or "cao nhất" in q):
            s = find_sample_with(["fields: company, high", "order by p.high desc"]) or find_sample_with(["fields: company, high", "order by p.high asc"])
            if s:
                return s
        # Low
        if ("low" in q or "thấp nhất" in q):
            s = find_sample_with(["fields: company, low", "order by p.low desc"]) or find_sample_with(["fields: company, low", "order by p.low asc"])
            if s:
                return s
        # Volume
        if ("volume" in q or "khối lượng" in q):
            s = find_sample_with(["fields: company, volume", "order by p.volume desc"]) or find_sample_with(["fields: company, volume", "order by p.volume asc"])
            if s:
                return s
        # Dividends
        if ("dividend" in q or "cổ tức" in q):
            s = find_sample_with(["fields: company, dividends", "order by p.dividends desc"]) or find_sample_with(["fields: company, dividends", "order by p.dividends asc"])
            if s:
                return s
        # Stock splits
        if ("stock split" in q or "split ratio" in q or "chia tách" in q or "tách cổ phiếu" in q):
            s = find_sample_with(["fields: company, stock_splits", "order by p.stock_splits desc"]) or find_sample_with(["fields: company, stock_splits", "order by p.stock_splits asc"])
            if s:
                return s

    # 1) Factual, medium theo năm ưu tiên tiếp nhưng chỉ khi có năm và KHÔNG có ngày đầy đủ
    # 1.a) Highest closing price in {year}
    if ("highest closing price" in q or ("cao nhất" in q and "đóng cửa" in q)) and has_year and not has_date:
        s = find_sample_with(["order by close desc", "strftime('%y', date) = :year".replace("%y", "%Y")])
        if s:
            return s
    # 1.b) Lowest closing price in {year}
    if ("lowest closing price" in q or ("thấp nhất" in q and "đóng cửa" in q)) and has_year and not has_date:
        s = find_sample_with(["order by close asc", "strftime('%y', date) = :year".replace("%y", "%Y")])
        if s:
            return s
    # 1.c) How many dividends in {year}
    if ("how many dividends" in q or "bao nhiêu lần cổ tức" in q or ("dividends" in q and "in" in q and has_year)) and has_year:
        s = find_sample_with(["count(*) as dividends_count", "dividends > 0"])
        if s:
            return s
    # 1.d) Dividend per share on {date}
    if ("dividend per share" in q or ("cổ tức" in q and ("ngày" in q or "vào" in q))) and has_date:
        s = find_sample_with(["select dividends as dividend_per_share", "date(:date)"])
        if s:
            return s
    # 1.e) Stock split date and ratio
    if ("stock split" in q or "chia tách" in q or "tách cổ phiếu" in q):
        s = find_sample_with(["split_ratio", "stock splits"])
        if s:
            return s

    # 2) Factual, easy theo ngày
    if ("closing price" in q or "giá đóng cửa" in q) and has_date and not has_date_range and not (t1 and t2) and ("change" not in q and "from" not in q and "to" not in q):
        s = find_sample_with(["select close", "date(:date)"])
        if s:
            return s
    if ("opening price" in q or "giá mở cửa" in q) and has_date and not has_date_range and not (t1 and t2):
        s = find_sample_with(["select open", "date(:date)"])
        if s:
            return s
    if ("highest price" in q or "giá cao nhất" in q) and has_date and not has_date_range and not (t1 and t2):
        s = find_sample_with(["select high", "date(:date)"])
        if s:
            return s
    if ("lowest price" in q or "giá thấp nhất" in q) and has_date and not has_date_range and not (t1 and t2):
        s = find_sample_with(["select low", "date(:date)"])
        if s:
            return s
    if ("trading volume" in q or "khối lượng" in q) and has_date and not has_date_range and not (t1 and t2):
        s = find_sample_with(["select volume", "date(:date)"])
        if s:
            return s

    # 3) Analytical: averages, totals, quarters, half-year
    if has_year and ticker is not None:
        # Total trading volume in year
        if ("total trading volume" in q or ("tổng" in q and "khối lượng" in q)):
            s = find_sample_with(["sum(volume) as total_volume", "strftime('%Y', date) = :year"])
            if s:
                return s
        # Average closing price in month
        if ("average closing price" in q or "trung bình" in q) and has_date and ("month" in q or "tháng" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) = :month"])
            if s:
                return s
        # Average closing price in quarter
        if ("average closing price" in q or "trung bình" in q) and ("q1" in q or "q2" in q or "q3" in q or "q4" in q or "quarter" in q or "quý" in q or "first quarter" in q):
            s = find_sample_with(["avg_close", ":quarter"]) or find_sample_with(["avg_close", "case "]) or find_sample_with(["avg_close", "strftime('%Y', date) = :year"]) 
            if s:
                return s
        # Average daily trading volume
        if ("average daily trading volume" in q or "khối lượng trung bình" in q):
            s = find_sample_with(["avg_volume", "avg(volume)"])
            if s:
                return s
        # Average closing price from month X to month Y
        if ("average closing price" in q or "trung bình" in q) and ("from" in q or "through" in q or "đến" in q or "den" in q or "-" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) between :start_month and :end_month"]) or find_sample_with(["avg_close", ":start_month"]) 
            if s:
                return s
        # Percentage increase in year
        if ("percentage" in q or "phần trăm" in q) and ("increase" in q or "tăng" in q):
            s = find_sample_with(["percentage_increase", "with year_prices"])
            if s:
                return s
        # Second half average
        if ("second half" in q or "nửa cuối" in q) and ("average" in q or "trung bình" in q):
            s = find_sample_with(["avg_close", "strftime('%m', date) in ('07', '08', '09', '10', '11', '12')"])
            if s:
                return s

    # 3.c) Index-level: average dividend yield for DJIA as a whole
    if ("dividend yield" in q or "lợi suất cổ tức" in q) and ("djia" in q or "as a whole" in q or "toàn bộ" in q or "toan bo" in q):
        s = find_sample_with(["avg_dividend_yield", "from companies"]) or find_sample_with(["avg(dividend_yield)", "from companies"]) 
        if s:
            return s

    # 3.bis) Company metadata factual easy: sector and ticker symbol
    if ticker is not None:
        # Sector of company
        if ("which sector" in q or "sector" in q or "thuộc ngành" in q):
            s = find_sample_with(["select sector", "from companies"]) or find_sample_with(["fields: sector", "from companies"])
            if s:
                return s
        # Ticker symbol of company
        if ("ticker symbol" in q or "mã cổ phiếu" in q or "mã" in q):
            s = find_sample_with(["fields: symbol"]) or find_sample_with([":ticker as symbol"]) or find_sample_with(["select :ticker as symbol"]) 
            if s:
                return s

    # 4) Fallback for other analytical patterns
    key_map = [
        ("median", "median_close"),
        ("trung vị", "median_close"),
    ]
    for key, signature in key_map:
        if key in q:
            for s in samples:
                if signature.lower() in s.lower():
                    return s

    # 4) Comparative, difficult: percentage/absolute changes over time periods
    if has_year and not has_date and not (t1 and t2):
        # Largest percentage increase in {year}
        if ("largest percentage increase" in q or "tỷ lệ tăng" in q) and ("stock price" in q or "cổ phiếu" in q):
            s = find_sample_with(["percentage_change", "with price_changes", "max(close) - min(close)"])
            if s:
                return s
        # Largest absolute increase in {year}
        if ("largest absolute increase" in q or "mức tăng tuyệt đối" in q) and ("dollars" in q or "usd" in q):
            s = find_sample_with(["absolute_change", "with price_changes", "max(close) - min(close)"])
            if s:
                return s
        # Largest percentage decline in {year}
        if ("largest percentage decline" in q or "tỷ lệ giảm" in q) and ("stock price" in q or "cổ phiếu" in q):
            s = find_sample_with(["percentage_decline", "with price_changes", "min(close) - max(close)"])
            if s:
                return s

    # 5) Price change between two specific dates (ưu tiên trước easy theo ngày)
    if ("change from" in q or "thay đổi từ" in q or ("from" in q and "to" in q)):
        s = find_sample_with(["price_change", "start_price", "end_price", "cross join"])
        if s:
            return s

    # 6) Comparative, medium: lowest/highest closing price on a date (returns company + close)
    if has_date and not (t1 and t2):
        # lowest closing price on {date}
        s = find_sample_with(["fields: company, close", "order by p.close asc", "limit 1"]) or find_sample_with(["join companies", "order by p.close asc", "limit 1"])
        if s:
            return s
        # highest closing price on {date}
        s = find_sample_with(["fields: company, close", "order by p.close desc", "limit 1"]) or find_sample_with(["join companies", "order by p.close desc", "limit 1"])
        if s:
            return s

    return None

def match_sql_template(state: Dict[str, Any]) -> Dict[str, Any]:
    sql = match_sample(state.get("question", ""))
    used_sample = sql is not None
    return {**state, "sql": sql, "used_sample": used_sample}


