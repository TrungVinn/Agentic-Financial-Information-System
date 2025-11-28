from typing import Dict, Any, Optional, List
import re
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from config import SQL_SAMPLES_FILE
from nodes.utils import normalize_text, extract_ticker
from nodes.chart_generator import build_chart_sql

# Load environment variables
load_dotenv()

# Setup Gemini API key
if os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

def load_sql_samples() -> List[str]:
    """Load SQL samples từ file."""
    if not SQL_SAMPLES_FILE.exists():
        return []
    
    text = SQL_SAMPLES_FILE.read_text(encoding="utf-8")
    statements = [s.strip() + ";" for s in re.split(r";\s*\n", text) if s.strip()]
    
    return statements


def validate_and_find_sql_with_llm(question: str, sql_samples: List[str]) -> Optional[str]:
    """Dùng LLM duy nhất để tìm SQL sample phù hợp. Nếu không có, trả về None."""
    if not sql_samples:
        return None
    
    samples_text = "\n".join([f"{i+1}. {sql}" for i, sql in enumerate(sql_samples)])
    
    prompt = f"""
Bạn là chuyên gia SQL của hệ thống Agentic Financial Information. Nhiệm vụ: từ danh sách SQL mẫu dưới đây, chọn CHÍNH XÁC một câu lệnh phù hợp nhất với câu hỏi.

CÂU HỎI: {question}

DANH SÁCH SQL MẪU (phải đọc toàn bộ trước khi quyết định):
{samples_text}

YÊU CẦU BẮT BUỘC:
- Chỉ chọn SQL nếu cấu trúc, bộ field SELECT, điều kiện WHERE, parameters (:ticker, :date, ...) hoàn toàn khớp với câu hỏi.
- Nếu câu hỏi cần 2 công ty, SQL phải có :ticker_a/:ticker_b hoặc logic tương ứng.
- Nếu cần theo ngày, SQL phải dùng date = CAST(:date AS DATE); theo năm dùng TO_CHAR(date,'YYYY') = :year.
- Tuyệt đối không chọn SQL chỉ "gần giống".

CÁCH TRẢ LỜI:
- Nếu tìm được, trả lời: FOUND: [index]; index bắt đầu từ 1 theo danh sách trên.
- Nếu không có SQL nào phù hợp 100%, trả lời: NO_MATCH.

Chỉ trả lời: FOUND: n hoặc NO_MATCH."""

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            max_tokens=200
        )
        response = llm.invoke(prompt)
        result = (response.content or "").strip()
        if result.startswith("FOUND:"):
            try:
                idx_str = result.split(":")[1].strip()
                idx = int(idx_str) - 1
                if 0 <= idx < len(sql_samples):
                    return sql_samples[idx]
            except (ValueError, IndexError):
                return None
        elif result == "NO_MATCH":
            return None
        return None
    except Exception as e:
        print(f"LLM validation error: {e}")
        return None


def match_sample(question: str) -> Optional[str]:
    """Chỉ dựa vào LLM để tìm SQL sample phù hợp."""
    sql_samples = load_sql_samples()
    return validate_and_find_sql_with_llm(question, sql_samples)

def match_sql_template(state: Dict[str, Any]) -> Dict[str, Any]:
    """Trích xuất ticker và tìm SQL template phù hợp với câu hỏi."""
    question = state.get("question", "")
    needs_chart = state.get("needs_chart", False)
    chart_request = state.get("chart_request")
    chart_type = state.get("chart_type")
    complexity = state.get("complexity", {})
    
    # Trích xuất ticker (gộp logic từ alias_resolver)
    ticker = extract_ticker(question)
    
    # Kiểm tra nếu câu hỏi về tất cả DJIA companies
    q = normalize_text(question)
    is_all_companies = (
        complexity.get("involves_multiple_companies", False) or
        any(phrase in q for phrase in [
            "all companies", "all djia", "each company", "each djia company",
            "tất cả công ty", "mỗi công ty", "for all djia", "for each djia"
        ])
    )
    
    if needs_chart:
        sql = build_chart_sql(question, chart_type, chart_request, ticker)
        return {**state, "ticker": ticker, "sql": sql, "used_sample": False}
    
    # Nếu câu hỏi về tất cả companies, force dùng LLM thay vì template
    if is_all_companies:
        return {**state, "ticker": None, "sql": None, "used_sample": False, "force_llm": True}
    
    if state.get("force_llm"):
        return {**state, "ticker": ticker, "sql": None, "used_sample": False}
    
    # Tìm SQL template (chỉ khi không phải all companies)
    sql = match_sample(question)
    used_sample = sql is not None
    
    return {**state, "ticker": ticker, "sql": sql, "used_sample": used_sample}


