from typing import Dict, Any, Optional
import os
import pandas as pd
from google import genai as google_genai
from dotenv import load_dotenv

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

def generate_answer_with_llm(question: str, sql: str, df: pd.DataFrame) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = google_genai.Client(api_key=api_key)
    
    # Chuẩn bị dữ liệu để hiển thị cho LLM
    if df.empty:
        data_summary = "Không có dữ liệu phù hợp."
    else:
        # Chuyển DataFrame thành text dễ đọc
        data_summary = df.to_string(index=False)
        if len(data_summary) > 1000:  # Giới hạn độ dài
            data_summary = df.head(10).to_string(index=False) + "\n... (còn nhiều dòng khác)"
    
    system = (
        "Bạn là trợ lý phân tích dữ liệu tài chính DJIA. "
        "Dựa trên câu hỏi của user và kết quả SQL, hãy đưa ra câu trả lời ngắn gọn, chính xác.\n\n"
        "Quy tắc:\n"
        "- Không bịa câu trả lời\n"
        "- Trả lời ngắn gọn, đi thẳng vào vấn đề\n"
        "- Sử dụng số liệu cụ thể từ kết quả\n"
        "- Nếu là giá cổ phiếu, thêm ký hiệu $ và làm tròn 2 chữ số thập phân\n"
        "- Nếu là phần trăm, thêm ký hiệu %\n"
        "- Nếu không có dữ liệu, nói rõ\n"
        "- Trả lời bằng ngôn ngữ giống câu hỏi\n"
    )
    
    prompt_text = (
        f"{system}\n"
        f"Câu hỏi: {question}\n\n"
        f"SQL đã chạy: {sql}\n\n"
        f"Kết quả:\n{data_summary}\n\n"
        f"Hãy trả lời câu hỏi dựa trên kết quả trên:"
    )
    
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt_text,
    )
    
    answer = (resp.text or "Không thể tạo câu trả lời.").strip()
    return answer

def summarize_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    sql = state.get("sql", "")
    df = state.get("df")
    
    if df is None:
        answer = "Không có dữ liệu để phân tích."
    else:
        answer = generate_answer_with_llm(question, sql, df)
    
    return {**state, "answer": answer}


