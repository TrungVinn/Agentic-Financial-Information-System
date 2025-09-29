import os
import re
import json
import sqlite3
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from google import genai as google_genai

from config import DB_PATH, SQL_SAMPLES_FILE, DJIA_COMPANIES_CSV


load_dotenv()

if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

@dataclass
class AgentResult:
    sql: str
    df: pd.DataFrame
    answer: str
    used_sample: bool


COMPANY_ALIASES: Dict[str, str] = {}


def _canonicalize_company_name(name: str) -> str:
    name_l = name.lower()
    # Loại bỏ (the)
    name_l = name_l.replace("(the)", " ")
    # Ký tự đặc biệt → khoảng trắng
    name_l = re.sub(r"[^a-z0-9]+", " ", name_l)
    # Bỏ từ phổ biến
    stop = {"inc", "incorporated", "corporation", "corp", "company", "co", "plc", "the"}
    tokens = [t for t in name_l.split() if t and t not in stop]
    return " ".join(tokens).strip()


def load_company_aliases() -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    # 1) Ưu tiên đọc từ CSV companies
    try:
        if DJIA_COMPANIES_CSV.exists():
            df = pd.read_csv(DJIA_COMPANIES_CSV)
            for _, row in df.iterrows():
                symbol = str(row.get("symbol") or row.get("Symbol") or "").strip()
                name = str(row.get("name") or row.get("Name") or "").strip()
                if not symbol:
                    continue
                # alias theo ticker
                aliases[symbol.lower()] = symbol
                # alias theo tên chuẩn hóa
                if name:
                    aliases[_canonicalize_company_name(name)] = symbol
    except Exception:
        pass

    # 2) Bổ sung các biến thể tên thông dụng trong hỏi đáp
    manual = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "boeing": "BA",
        "disney": "DIS",
        "coca cola": "KO",
        "cocacola": "KO",
        "ibm": "IBM",
        "verizon": "VZ",
        "unitedhealth": "UNH",
        "unitedhealth group": "UNH",
        "walgreens": "WBA",
        "walgreens boots alliance": "WBA",
        "chevron": "CVX",
        "american express": "AXP",
        "amgen": "AMGN",
        "caterpillar": "CAT",
        "honeywell": "HON",
        "mcdonald’s": "MCD",
        "mcdonalds": "MCD",
        "nike": "NKE",
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "johnson & johnson": "JNJ",
        "home depot": "HD",
        "dow": "DOW",
        "salesforce": "CRM",
        "cisco": "CSCO",
        "visa": "V",
        "procter & gamble": "PG",
        "merck": "MRK",
        "travellers": "TRV", 
        "travelers": "TRV",
        "walmart": "WMT",
        "three m": "MMM",
        "3m": "MMM",
        "goldman sachs": "GS",
    }
    for k, v in manual.items():
        aliases[k] = v

    return aliases


# Khởi tạo alias khi import
COMPANY_ALIASES = load_company_aliases()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_ticker(question: str) -> Optional[str]:
    q = normalize_text(question)
    # Nếu user đưa mã
    m = re.search(r"\b([A-Z]{2,5})\b", question)
    if m:
        return m.group(1)
    for name, ticker in COMPANY_ALIASES.items():
        if name in q:
            return ticker
    return None


def extract_date_parts(question: str) -> Dict[str, str]:
    # Hỗ trợ định dạng: March 15, 2024; 2024-03-15; 15/03/2024; 15-03-2024
    q = question
    # Chuẩn hóa tháng tiếng Anh → số
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),\s*(\d{4})", q, re.I)
    if m:
        month = months[m.group(1).lower()]
        day = f"{int(m.group(2)):02d}"
        year = m.group(3)
        return {"date": f"{year}-{month}-{day}", "year": year, "month": month}

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", q)
    if m:
        return {"date": f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "year": m.group(1), "month": m.group(2)}

    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", q)
    if m:
        day = f"{int(m.group(1)):02d}"
        month = f"{int(m.group(2)):02d}"
        year = m.group(3)
        return {"date": f"{year}-{month}-{day}", "year": year, "month": month}

    # Bắt năm đơn lẻ
    m = re.search(r"(20\d{2})", q)
    if m:
        return {"year": m.group(1)}
    return {}


def extract_date_range(question: str) -> Tuple[Optional[str], Optional[str]]:
    """Thử bắt 2 mốc thời gian dạng from ... to ... và trả về (start_date, end_date) ISO yyyy-mm-dd nếu nhận diện được."""
    q = question
    # Tìm tất cả pattern ngày phổ biến trong câu
    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),\s*(\d{4})",
    ]
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    found: List[str] = []
    for pat in patterns:
        for m in re.finditer(pat, q, re.I):
            if len(m.groups()) == 3 and pat == patterns[0]:
                found.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
            elif len(m.groups()) == 3 and pat == patterns[1]:
                day = f"{int(m.group(1)):02d}"; month = f"{int(m.group(2)):02d}"; year = m.group(3)
                found.append(f"{year}-{month}-{day}")
            elif len(m.groups()) == 3 and pat == patterns[2]:
                month = months[m.group(1).lower()]; day = f"{int(m.group(2)):02d}"; year = m.group(3)
                found.append(f"{year}-{month}-{day}")
    if len(found) >= 2:
        return found[0], found[1]
    return None, None


def extract_quarter(question: str) -> Optional[int]:
    """Nhận diện quý (Q1..Q4) từ câu hỏi: 'Q1', 'quarter 1', 'quý 1', hoặc dải tháng (Jan-Mar...)."""
    q = normalize_text(question)
    # Dạng Q1, Q2, ...
    m = re.search(r"\bq([1-4])\b", q)
    if m:
        return int(m.group(1))
    # Dạng 'quarter 1' hoặc 'quý 1' (chấp nhận 'quy' không dấu)
    m = re.search(r"\b(quarter|qu(?:ý|y))\s*([1-4])\b", q)
    if m:
        return int(m.group(2))
    # Dạng 'first/second/third/fourth quarter' hoặc 'quarter first/...'
    word_to_num = {
        "first": 1, "1st": 1, "one": 1,
        "second": 2, "2nd": 2, "two": 2,
        "third": 3, "3rd": 3, "three": 3,
        "fourth": 4, "4th": 4, "four": 4,
        # tiếng Việt
        "thu nhat": 1, "thứ nhất": 1, "dau tien": 1, "đầu tiên": 1,
        "thu hai": 2, "thứ hai": 2,
        "thu ba": 3, "thứ ba": 3,
        "thu tu": 4, "thứ tư": 4,
    }
    # quarter <word>
    m = re.search(r"\bquarter\s+(first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\b", q)
    if m:
        return word_to_num.get(m.group(1), None)
    # <word> quarter
    m = re.search(r"\b(first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\s+quarter\b", q)
    if m:
        return word_to_num.get(m.group(1), None)
    # quý <số La Mã> (I, II, III, IV)
    m = re.search(r"\bqu(?:ý|y)\s*(i{1,3}|iv)\b", q)
    if m:
        roman = m.group(1)
        roman_map = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
        return roman_map.get(roman, None)
    # Dạng tháng: Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec
    q_simple = q.replace("–", "-")
    tokens = re.split(r"[^a-z]+", q_simple)
    tokens = [t for t in tokens if t]
    has = set(tokens)
    q1 = {"jan", "january", "feb", "february", "mar", "march"}
    q2 = {"apr", "april", "may", "jun", "june"}
    q3 = {"jul", "july", "aug", "august", "sep", "september"}
    q4 = {"oct", "october", "nov", "november", "dec", "december"}
    if has & q1:
        return 1
    if has & q2:
        return 2
    if has & q3:
        return 3
    if has & q4:
        return 4
    return None

def extract_month_range(question: str) -> Tuple[Optional[str], Optional[str]]:
    """Nhận diện khoảng tháng: from/through {monthX} to {monthY}, {monthX}-{monthY}, hoặc "tháng X đến tháng Y".
    Trả về (start_month, end_month) dạng 'MM'."""
    q = normalize_text(question)
    month_map = {
        "jan": "01", "january": "01", "thang 1": "01",
        "feb": "02", "february": "02", "thang 2": "02",
        "mar": "03", "march": "03", "thang 3": "03",
        "apr": "04", "april": "04", "thang 4": "04",
        "may": "05", "thang 5": "05",
        "jun": "06", "june": "06", "thang 6": "06",
        "jul": "07", "july": "07", "thang 7": "07",
        "aug": "08", "august": "08", "thang 8": "08",
        "sep": "09", "september": "09", "thang 9": "09",
        "oct": "10", "october": "10", "thang 10": "10",
        "nov": "11", "november": "11", "thang 11": "11",
        "dec": "12", "december": "12", "thang 12": "12",
    }
    q2 = q.replace("–", "-").replace("—", "-")
    patterns = [
        r"from\s+([a-z]+)\s+(?:to|through)\s+([a-z]+)",
        r"\b([a-z]+)\s*-\s*([a-z]+)\b",
        r"thang\s+([0-9]{1,2})\s+(?:den|đến)\s+thang\s+([0-9]{1,2})",
    ]
    for pat in patterns:
        m = re.search(pat, q2)
        if not m:
            continue
        a = m.group(1)
        b = m.group(2)
        if a.isalpha():
            a_norm = month_map.get(a, month_map.get(a[:3], None))
        else:
            a_norm = f"{int(a):02d}" if a.isdigit() else None
        if b.isalpha():
            b_norm = month_map.get(b, month_map.get(b[:3], None))
        else:
            b_norm = f"{int(b):02d}" if b.isdigit() else None
        if a_norm and b_norm:
            return a_norm, b_norm
    return None, None
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


def generate_sql_with_llm(question: str, feedback: Optional[str] = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = google_genai.Client(api_key=api_key)
    system = (
        "Bạn là trợ lý tạo SQL cho SQLite. Có 2 bảng:\n"
        "- prices(date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, dividends REAL, stock_splits REAL, ticker TEXT)\n"
        "- companies(symbol TEXT, name TEXT, sector TEXT, industry TEXT, country TEXT, website TEXT, market_cap REAL, pe_ratio REAL, dividend_yield REAL, week_52_high REAL, week_52_low REAL, description TEXT)\n\n"
        "Quy tắc bắt buộc:\n"
        "- Trả về CHỈ MỘT câu SQL hợp lệ cho SQLite.\n"
        "- Dùng tham số kiểu :ticker, :date, :year, :month nếu phù hợp.\n"
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


def run_sql(sql: str, params: Dict[str, Any]) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def derive_answer(df: pd.DataFrame) -> str:
    if df.empty:
        return "Không có dữ liệu phù hợp."
    # Lấy ô đầu tiên nếu có cột duy nhất
    if df.shape[1] == 1:
        val = df.iloc[0, 0]
        if isinstance(val, (int, float)):
            return f"{val}"
        return str(val)
    # Nếu có cột close/volume hay max_close...
    for col in ["close", "open", "high", "low", "volume", "max_close", "min_close", "avg_close", "median_close", "a_close", "b_close"]:
        if col in df.columns:
            return str(df[col].iloc[0])
    # Fallback
    return str(df.iloc[0].to_dict())


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


def answer_question(question: str) -> AgentResult:
    ticker = extract_ticker(question)
    params = build_params(question, ticker)

    sql = match_sample(question)
    used_sample = sql is not None
    if sql:
        df = run_sql(sql, params)
        ans = derive_answer(df)
        return AgentResult(sql=sql, df=df, answer=ans, used_sample=used_sample)

    # Không có mẫu: gọi Gemini, thử tối đa 3 lần với phản hồi lỗi
    last_error: Optional[str] = None
    last_sql: str = ""
    for _ in range(3):
        gen_sql = generate_sql_with_llm(question, feedback=last_error)
        last_sql = gen_sql
        try:
            df = run_sql(gen_sql, params)
            ans = derive_answer(df)
            return AgentResult(sql=gen_sql, df=df, answer=ans, used_sample=False)
        except Exception as e:
            last_error = f"{e}"
            continue

    # Thất bại sau 3 lần
    empty = pd.DataFrame()
    return AgentResult(sql=last_sql, df=empty, answer="Xin lỗi, tôi chưa thể trả lời câu hỏi này.", used_sample=False)


