from typing import Dict, Any, List
from datetime import date, datetime
import json
import os

import pandas as pd
from dotenv import load_dotenv
from google import generativeai as google_genai

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def _normalize_value(val: Any) -> Any:
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, (pd.Series, pd.DataFrame)):
        return val.to_dict()
    return val


def _format_dataframe(df: pd.DataFrame, max_rows: int = 25) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    trimmed = df.head(max_rows).copy()
    trimmed = trimmed.applymap(_normalize_value)
    return trimmed.to_dict(orient="records")


def _derive_answer_fallback(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "Không có dữ liệu phù hợp."
    if df.shape[1] == 1:
        val = df.iloc[0, 0]
        if isinstance(val, (int, float)):
            return f"{val}"
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, date):
            return val.isoformat()
        return str(val)
    for col in ["close", "open", "high", "low", "volume", "max_close", "min_close", "avg_close", "median_close", "a_close", "b_close"]:
        if col in df.columns:
            val = df[col].iloc[0]
            if isinstance(val, (pd.Timestamp, datetime)):
                return val.strftime("%Y-%m-%d")
            if isinstance(val, date):
                return val.isoformat()
            return str(val)
    row = df.iloc[0].to_dict()
    for k, v in row.items():
        if isinstance(v, (pd.Timestamp, datetime)):
            row[k] = v.strftime("%Y-%m-%d")
        elif isinstance(v, date):
            row[k] = v.isoformat()
    return str(row)


def _summarize_with_llm(question: str, df: pd.DataFrame, sql: str = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return _derive_answer_fallback(df)
    google_genai.configure(api_key=api_key)
    data_preview = _format_dataframe(df)
    summary_input = json.dumps(data_preview, ensure_ascii=False, indent=2)
    
    system_prompt = (
        "Bạn là trợ lý phân tích tài chính. Hãy đọc câu hỏi và kết quả truy vấn SQL, "
        f"Nếu {question} là tiếng Anh, hãy LUÔN LUÔN trả lời bằng tiếng Anh. Nếu {question} là tiếng Việt, hãy LUÔN LUÔN trả lời bằng tiếng Việt. "
        "Trả lời ngắn gọn, rõ ràng (làm tròn số nếu cần) và nêu tên công ty/mốc thời gian chính xác. "
        "Nếu dữ liệu rỗng, hãy nói rằng không tìm thấy dữ liệu phù hợp. "
        "Khi con số là âm, hãy mô tả bằng lời (ví dụ: '-62%' -> 'giảm 62%', '-74.76' USD -> 'giảm 74.76 USD'). "
        "Khi con số là dương, dùng phrasing 'tăng ...' hoặc 'là ...' tùy ngữ cảnh. "
        "Tránh lặp lại dấu âm trong câu trả lời; hãy diễn đạt theo nghĩa tăng/giảm để người đọc dễ hiểu."
    )
    
    prompt = (
        f"{system_prompt}\n\n"
        f"Câu hỏi: {question}\n"
        f"SQL đã chạy: {sql or 'N/A'}\n"
        f"Số dòng kết quả: {len(data_preview)}\n"
        f"Dữ liệu (tối đa 25 dòng):\n{summary_input}\n\n"
        "Trả lời:"
    )
    
    model = google_genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    answer = (response.text or "").strip()
    if not answer:
        return _derive_answer_fallback(df)
    return answer


def summarize_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    df = state.get("df")
    error = state.get("error")
    question = state.get("question", "")
    sql = state.get("sql")
    
    if error:
        answer = f"Không thể thực thi truy vấn do lỗi: {error}"
        return {**state, "answer": answer}
    
    try:
        answer = _summarize_with_llm(question, df, sql)
    except Exception as e:
        fallback = _derive_answer_fallback(df)
        # Nếu đã có biểu đồ vẽ thành công, không hiển thị thông báo lỗi LLM
        chart = state.get("chart")
        if chart is not None:
            answer = fallback
        else:
            answer = f"{fallback} (LLM fallback: {e})"
    
    return {**state, "answer": answer}