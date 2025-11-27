import re
import sqlite3
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
from config import DB_PATH, SQL_SAMPLES_FILE, DJIA_COMPANIES_CSV

COMPANY_ALIASES: Dict[str, str] = {}

def _canonicalize_company_name(name: str) -> str:
    name_l = name.lower()
    name_l = name_l.replace("(the)", " ")
    name_l = re.sub(r"[^a-z0-9]+", " ", name_l)
    stop = {"inc", "incorporated", "corporation", "corp", "company", "co", "plc", "the"}
    tokens = [t for t in name_l.split() if t and t not in stop]
    return " ".join(tokens).strip()

def load_company_aliases() -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    try:
        if DJIA_COMPANIES_CSV.exists():
            df = pd.read_csv(DJIA_COMPANIES_CSV)
            for _, row in df.iterrows():
                symbol = str(row.get("symbol") or row.get("Symbol") or "").strip()
                name = str(row.get("name") or row.get("Name") or "").strip()
                if not symbol:
                    continue
                aliases[symbol.lower()] = symbol
                if name:
                    aliases[_canonicalize_company_name(name)] = symbol
    except Exception:
        pass

    manual = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "boeing": "BA",
        "disney": "DIS",
        "coca-cola": "KO",
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

COMPANY_ALIASES = load_company_aliases()

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_ticker(question: str) -> Optional[str]:
    q = normalize_text(question)
    
    # Bỏ qua các từ không phải ticker
    ignore_words = {"djia", "plot", "pie", "bar", "scatter", "heatmap", "chart", "graph"}
    if any(word in q for word in ignore_words):
        # Nếu có từ "all companies", "each company", "all DJIA" thì không extract ticker
        if any(phrase in q for phrase in ["all companies", "each company", "all djia", "each djia company", 
                                          "tất cả công ty", "mỗi công ty"]):
            return None
    
    # Tìm ticker từ alias trước (ưu tiên hơn)
    for name, ticker in COMPANY_ALIASES.items():
        pattern = r"\b" + re.escape(name) + r"\b"
        if re.search(pattern, q):
            return ticker
    
    # Tìm ticker từ pattern (chỉ khi không có từ ignore)
    m = re.search(r"\b([A-Z]{2,5})\b", question)
    if m:
        ticker_candidate = m.group(1)
        # Bỏ qua nếu là từ ignore
        if ticker_candidate.lower() not in ignore_words:
            return ticker_candidate
    
    return None


def extract_date_parts(question: str) -> Dict[str, str]:
    q = question
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
    # Thêm pattern cho "March 2025" (tháng + năm)
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})", q, re.I)
    if m:
        month = months[m.group(1).lower()]
        year = m.group(2)
        return {"year": year, "month": month}
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", q)
    if m:
        return {"date": f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "year": m.group(1), "month": m.group(2)}
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", q)
    if m:
        day = f"{int(m.group(1)):02d}"
        month = f"{int(m.group(2)):02d}"
        year = m.group(3)
        return {"date": f"{year}-{month}-{day}", "year": year, "month": month}
    m = re.search(r"(20\d{2})", q)
    if m:
        return {"year": m.group(1)}
    return {}


def extract_date_range(question: str) -> Tuple[Optional[str], Optional[str]]:
    q = question
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
    q = normalize_text(question)
    m = re.search(r"\bq([1-4])\b", q)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(quarter|qu(?:ý|y))\s*([1-4])\b", q)
    if m:
        return int(m.group(2))
    word_to_num = {
        "first": 1, "1st": 1, "one": 1,
        "second": 2, "2nd": 2, "two": 2,
        "third": 3, "3rd": 3, "three": 3,
        "fourth": 4, "4th": 4, "four": 4,
        "thu nhat": 1, "thứ nhất": 1, "dau tien": 1, "đầu tiên": 1,
        "thu hai": 2, "thứ hai": 2,
        "thu ba": 3, "thứ ba": 3,
        "thu tu": 4, "thứ tư": 4,
    }
    m = re.search(r"\bquarter\s+(first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\b", q)
    if m:
        return word_to_num.get(m.group(1), None)
    m = re.search(r"\b(first|second|third|fourth|1st|2nd|3rd|4th|one|two|three|four)\s+quarter\b", q)
    if m:
        return word_to_num.get(m.group(1), None)
    m = re.search(r"\bqu(?:ý|y)\s*(i{1,3}|iv)\b", q)
    if m:
        roman = m.group(1)
        roman_map = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
        return roman_map.get(roman, None)
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




