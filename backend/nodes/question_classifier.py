"""
Question Classifier Node - Phân loại câu hỏi ngay từ đầu.

Node này phân tích câu hỏi và quyết định:
- SQL-related: Câu hỏi cần truy vấn database (giá, volume, số liệu)
- Other: Câu hỏi không liên quan SQL (kiến thức tổng quát, câu hỏi chung)

Sử dụng LLM để phân loại chính xác hơn so với pattern matching.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as google_genai

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def classify_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Question Classifier - Phân loại câu hỏi.
    
    Node này phân tích câu hỏi và quyết định:
    - is_sql_related: True nếu cần truy vấn SQL database
    - is_sql_related: False nếu là câu hỏi khác (kiến thức tổng quát, câu hỏi chung)
    
    Args:
        state: Dictionary chứa workflow state, cần có key "question"
        
    Returns:
        State mới với các key:
        - is_sql_related: Boolean - có liên quan SQL không
    """
    question = state.get("question", "")
    
    if not question or not question.strip():
        # Mặc định là SQL-related nếu không có câu hỏi
        return {**state, "is_sql_related": True}
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Fallback: mặc định là SQL-related
        print("Warning: No Gemini API key found. Defaulting to SQL-related.")
        return {**state, "is_sql_related": True}
    
    try:
        google_genai.configure(api_key=api_key)
        
        # Prompt để LLM phân loại câu hỏi
        prompt = f"""Bạn là một chuyên gia phân loại câu hỏi cho hệ thống tài chính.

Hệ thống có 2 loại câu hỏi:
1. SQL-RELATED: Câu hỏi yêu cầu dữ liệu cụ thể từ database
   Bao gồm:
   - Giá cổ phiếu, volume, số liệu cụ thể: "What was the price of Apple on 2024-01-15?", "Plot the volume", 
     "Compare prices of AAPL and MSFT", "Average closing price in 2024"
   - Metadata của công ty (website, sector, industry, country, market_cap, pe_ratio, dividend_yield, etc.):
     "Website of 3M Company?", "What is the sector of Apple?", "Market cap of Microsoft?", 
     "Dividend yield of Coca-Cola?", "Industry of Boeing?", "Country of IBM?"
   - Ticker symbol: "What is the ticker symbol for Apple?", "Symbol of Microsoft?"
   - So sánh số liệu, biểu đồ dữ liệu, truy vấn theo ngày tháng, ticker cụ thể
   
2. OTHER: Câu hỏi không cần SQL (kiến thức tổng quát, giải thích, định nghĩa, câu hỏi chung)
   Ví dụ: "What is DJIA?", "How does stock market work?", "Giải thích về thị trường chứng khoán",
          "What is a dividend?", "Tôi muốn biết về đầu tư", "How to invest in stocks?"

CÂU HỎI: {question}

NHIỆM VỤ: Xác định xem câu hỏi này có liên quan đến SQL database không.

QUY TẮC QUAN TRỌNG:
- ⚠️ TRẢ VỀ SQL nếu câu hỏi yêu cầu BẤT KỲ thông tin nào từ database, bao gồm:
  * Giá cả, volume, số liệu cụ thể
  * Metadata của công ty (website, sector, industry, country, market_cap, pe_ratio, dividend_yield, 
    week_52_high, week_52_low, description, ticker symbol)
  * So sánh số liệu, biểu đồ dữ liệu
  * Truy vấn theo ngày tháng, ticker cụ thể
  
- ⚠️ TRẢ VỀ OTHER CHỈ KHI câu hỏi hỏi về: khái niệm, định nghĩa, giải thích, kiến thức tổng quát, 
  cách thức hoạt động, câu hỏi chung KHÔNG cần dữ liệu cụ thể từ database

LƯU Ý: Câu hỏi về website, sector, industry, country, market_cap, pe_ratio, dividend_yield của một công ty cụ thể 
→ LUÔN LUÔN là SQL-RELATED (vì cần truy vấn từ bảng companies trong database)

CHỈ TRẢ LỜI: SQL hoặc OTHER (không có dấu chấm, không có giải thích thêm)"""

        model = google_genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        result = (response.text or "").strip().upper()
        
        # Parse kết quả
        is_sql_related = "SQL" in result
        
        return {
            **state,
            "is_sql_related": is_sql_related,
        }
            
    except Exception as e:
        print(f"Error in classify_question with LLM: {e}")
        # Fallback: mặc định là SQL-related
        return {**state, "is_sql_related": True}

