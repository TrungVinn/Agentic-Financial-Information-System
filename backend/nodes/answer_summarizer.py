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
    for col in [
        "close",
        "open",
        "high",
        "low",
        "volume",
        "max_close",
        "min_close",
        "avg_close",
        "median_close",
        "a_close",
        "b_close",
    ]:
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

    model = google_genai.GenerativeModel("gemini-2.5-flash-lite")
    response = model.generate_content(prompt)
    answer = (response.text or "").strip()
    if not answer:
        return _derive_answer_fallback(df)
    return answer


def _answer_general_question_with_llm(question: str) -> str:
    """
    Trả lời câu hỏi chung không liên quan SQL bằng LLM.
    
    Args:
        question: Câu hỏi từ người dùng
        
    Returns:
        Câu trả lời từ LLM
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Xin lỗi, tôi không thể trả lời câu hỏi này. Vui lòng kiểm tra API key."
    
    google_genai.configure(api_key=api_key)
    
    # Detect language
    vietnamese_chars = ['à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 
                        'â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ', 'è', 'é', 'ẻ', 'ẽ', 'ẹ',
                        'ê', 'ế', 'ề', 'ể', 'ễ', 'ệ', 'ì', 'í', 'ỉ', 'ĩ', 'ị',
                        'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ',
                        'ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ', 'ù', 'ú', 'ủ', 'ũ', 'ụ',
                        'ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự', 'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ', 'đ']
    is_vietnamese = any(char in question.lower() for char in vietnamese_chars)
    
    system_prompt = (
        "Bạn là trợ lý AI thông minh và hữu ích. "
        "Hãy trả lời câu hỏi một cách chính xác, rõ ràng và hữu ích. "
        f"{'Trả lời bằng tiếng Việt.' if is_vietnamese else 'Answer in English.'}"
    )
    
    prompt = f"{system_prompt}\n\nCâu hỏi: {question}\n\nTrả lời:"
    
    try:
        model = google_genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        answer = (response.text or "").strip()
        if not answer:
            return "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này."
        return answer
    except Exception as e:
        return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi: {str(e)}"


def _answer_with_rag_context(question: str, rag_context: List[Dict[str, Any]]) -> str:
    """
    Trả lời câu hỏi sử dụng LLM với context từ RAG.
    
    Args:
        question: Câu hỏi từ người dùng
        rag_context: List documents retrieved từ PDF
        
    Returns:
        Câu trả lời từ LLM với context từ PDF
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Không thể kết nối với LLM. Vui lòng kiểm tra API key."
    
    google_genai.configure(api_key=api_key)
    
    # Build context string với source attribution
    if rag_context:
        context_parts = []
        for i, doc in enumerate(rag_context, 1):
            source = doc.get("source", "unknown")
            content = doc.get("content", "")
            relevance = doc.get("relevance_score", 0)
            context_parts.append(
                f"[Document {i}] (Source: {source}, Relevance: {relevance:.2f})\n{content}"
            )
        context_text = "\n\n---\n\n".join(context_parts)
    else:
        context_text = "Không tìm thấy context phù hợp trong knowledge base."
    
    # Detect language
    vietnamese_chars = ['à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 
                        'â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ', 'è', 'é', 'ẻ', 'ẽ', 'ẹ',
                        'ê', 'ế', 'ề', 'ể', 'ễ', 'ệ', 'ì', 'í', 'ỉ', 'ĩ', 'ị',
                        'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ',
                        'ơ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ', 'ù', 'ú', 'ủ', 'ũ', 'ụ',
                        'ư', 'ứ', 'ừ', 'ử', 'ữ', 'ự', 'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ', 'đ']
    is_vietnamese = any(char in question.lower() for char in vietnamese_chars)
    
    system_prompt = f"""Bạn là trợ lý AI chuyên về thị trường chứng khoán và DJIA (Dow Jones Industrial Average).

RETRIEVED CONTEXT FROM PDF DOCUMENTS:
{context_text}

YÊU CẦU:
- Trả lời dựa trên context được cung cấp từ PDF documents
- Nếu context không đủ thông tin, hãy nói rõ và cung cấp kiến thức chung dựa trên context có sẵn
- {'Trả lời bằng tiếng Việt' if is_vietnamese else 'Answer in English'}
- Giữ câu trả lời ngắn gọn, rõ ràng, dễ hiểu
- Cite source documents khi có thể (ví dụ: "Theo tài liệu X...")
- Nếu câu hỏi về giá cụ thể của một cổ phiếu tại thời điểm nào đó, hãy hướng dẫn người dùng hỏi lại với format phù hợp"""

    prompt = f"{system_prompt}\n\nCâu hỏi: {question}\n\nTrả lời:"
    
    try:
        model = google_genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        answer = (response.text or "").strip()
        return answer if answer else "Không thể tạo câu trả lời."
    except Exception as e:
        return f"Lỗi khi gọi LLM: {str(e)}"


def summarize_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Answer Summarizer - Tạo câu trả lời tự nhiên.
    
    Xử lý 3 trường hợp:
    1. Câu hỏi SQL-related: Trả lời dựa trên kết quả SQL
    2. Câu hỏi Other + có RAG context: Trả lời dựa trên PDF documents
    3. Câu hỏi Other + không có RAG context: Giao cho LLM trả lời
    """
    df = state.get("df")
    error = state.get("error")
    question = state.get("question", "")
    sql = state.get("sql")

    # ========== TRƯỜNG HỢP 1: Câu hỏi không liên quan SQL (Other) ==========
    is_sql_related = state.get("is_sql_related", True)
    
    if not is_sql_related:
        # Câu hỏi loại Other - không cần SQL
        has_rag_context = state.get("has_rag_context", False)
        rag_context = state.get("rag_context", [])
        
        if has_rag_context and rag_context:
            # Có thông tin từ PDF, trả lời dựa trên RAG context
            try:
                answer = _answer_with_rag_context(question, rag_context)
                return {**state, "answer": answer}
            except Exception as e:
                # Fallback: Nếu lỗi khi dùng RAG context, chuyển sang LLM general
                print(f"Error answering with RAG context: {e}. Falling back to LLM general.")
                try:
                    answer = _answer_general_question_with_llm(question)
                    return {**state, "answer": answer}
                except Exception as e2:
                    answer = f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi. Lỗi: {str(e2)}"
                    return {**state, "answer": answer}
        else:
            # Không có thông tin trong PDF, giao cho LLM trả lời
            try:
                answer = _answer_general_question_with_llm(question)
                return {**state, "answer": answer}
            except Exception as e:
                answer = f"Xin lỗi, tôi không thể trả lời câu hỏi này. Lỗi: {str(e)}"
                return {**state, "answer": answer}
    
    # ========== TRƯỜNG HỢP 2: Câu hỏi SQL-related ==========
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
