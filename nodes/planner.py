"""
Query Planner Node - Phân tích độ phức tạp của câu hỏi.

Module này là bước đầu tiên trong workflow, phân tích câu hỏi người dùng để:
1. Xác định độ phức tạp (đơn giản vs multi-step)
2. Phát hiện yêu cầu vẽ biểu đồ
3. Phân loại câu hỏi (so sánh, tổng hợp, thống kê...)
4. Tạo execution plan cho câu hỏi phức tạp
"""

from typing import Dict, Any, Optional, List
import os
import re
import json
import google.generativeai as google_genai
from dotenv import load_dotenv
from nodes.utils import normalize_text, extract_ticker

# Load environment variables
load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def detect_query_complexity(question: str) -> Dict[str, Any]:
    """
    Phân tích câu hỏi để xác định độ phức tạp và yêu cầu.
    
    Args:
        question: Câu hỏi từ người dùng (tiếng Việt hoặc tiếng Anh)
        
    Returns:
        Dictionary chứa các thông tin:
        - is_multi_step: Câu hỏi có cần nhiều bước xử lý không
        - needs_chart: Có cần vẽ biểu đồ không
        - chart_type: Loại biểu đồ (line, candlestick, volume, comparison)
        - is_comparison: Có phải câu hỏi so sánh không
        - is_aggregation: Có phải câu hỏi tổng hợp (avg, sum, total...) không
        - is_statistical: Có phải phân tích thống kê (correlation, volatility...) không
        - time_series: Có phải dữ liệu theo thời gian không
        - involves_multiple_companies: Có liên quan nhiều công ty không
        
    Examples:
        >>> detect_query_complexity("Vẽ biểu đồ giá Apple")
        {'needs_chart': True, 'chart_type': 'line', ...}
        
        >>> detect_query_complexity("What was the closing price of Microsoft?")
        {'needs_chart': False, 'is_comparison': False, ...}
    """
    q = normalize_text(question)
    
    # Khởi tạo complexity object với các giá trị mặc định
    complexity = {
        "is_multi_step": False,           # Câu hỏi phức tạp nhiều bước
        "needs_chart": False,              # Cần vẽ biểu đồ
        "chart_type": None,                # Loại biểu đồ (nếu cần)
        "is_comparison": False,            # Câu hỏi so sánh
        "is_aggregation": False,           # Câu hỏi tổng hợp (avg, sum...)
        "is_statistical": False,           # Phân tích thống kê
        "time_series": False,              # Dữ liệu theo thời gian
        "involves_multiple_companies": False,  # Liên quan nhiều công ty
    }
    
    # ========== PHÁT HIỆN YÊU CẦU VẼ BIỂU ĐỒ ==========
    # Chỉ vẽ biểu đồ khi câu hỏi chứa từ "plot" hoặc "vẽ"
    chart_trigger_patterns = [r"\bplot\b", r"\bvẽ\b", r"\bve\b"]
    has_chart_trigger = any(re.search(pattern, q) for pattern in chart_trigger_patterns)
    has_explicit_chart_request = has_chart_trigger
    
    if has_chart_trigger:
        complexity["needs_chart"] = True
        
        # Xác định loại biểu đồ dựa trên từ khóa
        if any(word in q for word in ["candlestick", "nến", "nen", "ohlc"]):
            # Biểu đồ nến (Open-High-Low-Close)
            complexity["chart_type"] = "candlestick"
        elif any(word in q for word in ["volume", "khối lượng", "khoi luong"]) and has_explicit_chart_request:
            # Biểu đồ khối lượng giao dịch
            complexity["chart_type"] = "volume"
        elif any(word in q for word in ["compare", "so sánh", "so sanh", "comparison"]) and has_explicit_chart_request:
            # Biểu đồ so sánh nhiều cổ phiếu
            complexity["chart_type"] = "comparison"
        else:
            # Mặc định: biểu đồ đường (line chart)
            complexity["chart_type"] = "line"
    
    # ========== PHÂN LOẠI CÂU HỎI ==========
    
    # 1. Kiểm tra câu hỏi SO SÁNH
    # Ví dụ: "Which company had a higher closing price?"
    comparison_keywords = [
        "compare", "so sánh", "so sanh",
        "vs", "versus",
        "higher", "lower", "cao hơn", "cao hon", "thấp hơn", "thap hon",
        "which company"
    ]
    if any(keyword in q for keyword in comparison_keywords):
        complexity["is_comparison"] = True
    
    # 2. Kiểm tra câu hỏi TỔNG HỢP
    # Ví dụ: "What was the average closing price?", "Total volume?"
    aggregation_keywords = [
        "average", "total", "sum",
        "trung bình", "trung binh", "tổng", "tong",
        "median", "mean", "max", "min",
        "highest", "lowest"
    ]
    if any(keyword in q for keyword in aggregation_keywords):
        complexity["is_aggregation"] = True
    
    # 3. Kiểm tra phân tích THỐNG KÊ
    # Ví dụ: "Calculate volatility", "Correlation between..."
    statistical_keywords = [
        "correlation", "volatility", "standard deviation",
        "beta", "sharpe ratio",
        "tương quan", "tuong quan",
        "biến động", "bien dong",
        "độ lệch chuẩn"
    ]
    if any(keyword in q for keyword in statistical_keywords):
        complexity["is_statistical"] = True
        complexity["is_multi_step"] = True  # Thống kê luôn cần nhiều bước
    
    # 4. Kiểm tra TIME SERIES
    # Ví dụ: "from January to March", "during 2024", "between..."
    time_keywords = [
        "over time", "theo thời gian", "theo thoi gian",
        "from .* to",  # regex pattern
        "trong khoảng", "trong khoang",
        "during", "between"
    ]
    if any(re.search(keyword, q) for keyword in time_keywords):
        complexity["time_series"] = True
    
    # 5. Kiểm tra MULTI-COMPANY queries
    # Ví dụ: "all companies", "tất cả công ty"
    if "all companies" in q or "tất cả công ty" in q or "tat ca cong ty" in q:
        complexity["involves_multiple_companies"] = True
        complexity["is_multi_step"] = True
    
    # ========== XÁC ĐỊNH MULTI-STEP QUERY ==========
    # Câu hỏi được coi là multi-step nếu:
    # - Là phân tích thống kê
    # - Liên quan nhiều công ty
    # - Vừa so sánh vừa tổng hợp
    multi_step_indicators = [
        complexity["is_statistical"],
        complexity["involves_multiple_companies"],
        (complexity["is_comparison"] and complexity["is_aggregation"]),
    ]
    
    if any(multi_step_indicators):
        complexity["is_multi_step"] = True
    
    return complexity


def create_execution_plan(question: str, complexity: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Tạo kế hoạch thực thi chi tiết cho các câu hỏi phức tạp.
    
    Sử dụng Gemini AI để phân tích câu hỏi và tạo các bước thực thi.
    
    Args:
        question: Câu hỏi từ người dùng
        complexity: Dictionary chứa thông tin độ phức tạp từ detect_query_complexity()
        
    Returns:
        List các bước thực thi, mỗi bước có:
        - step_number: Số thứ tự bước
        - description: Mô tả bước
        - sql_needed: Có cần truy vấn SQL không
        - chart_needed: Có cần vẽ biểu đồ không
        
    Note:
        Nếu LLM gặp lỗi, trả về execution plan đơn giản (fallback)
    """
    # Cấu hình Gemini API
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    google_genai.configure(api_key=api_key)
    
    # System prompt cho LLM
    system = (
        "Bạn là một chuyên gia phân tích dữ liệu tài chính. "
        "Nhiệm vụ của bạn là phân tích câu hỏi và tạo kế hoạch thực thi từng bước.\n\n"
        "Quy tắc:\n"
        "- Phân tích câu hỏi thành các bước nhỏ\n"
        "- Mỗi bước nên có mục tiêu rõ ràng\n"
        "- Trả về định dạng JSON với cấu trúc:\n"
        '  {"steps": [{"step_number": 1, "description": "...", "sql_needed": true/false, "chart_needed": true/false}]}\n'
        "- Chỉ trả về JSON, không thêm giải thích\n"
    )
    
    # Tạo prompt với thông tin complexity
    prompt = (
        f"{system}\n"
        f"Câu hỏi: {question}\n\n"
        f"Độ phức tạp phát hiện:\n"
        f"- Multi-step: {complexity['is_multi_step']}\n"
        f"- Cần biểu đồ: {complexity['needs_chart']}\n"
        f"- So sánh: {complexity['is_comparison']}\n"
        f"- Tổng hợp: {complexity['is_aggregation']}\n"
        f"- Thống kê: {complexity['is_statistical']}\n\n"
        f"Hãy tạo kế hoạch thực thi:"
    )
    
    try:
        # Gọi Gemini AI
        model = google_genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        
        # Parse JSON response
        plan_text = resp.text.strip()
        
        # Xử lý markdown code blocks nếu LLM trả về
        if "```json" in plan_text:
            plan_text = plan_text.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_text:
            plan_text = plan_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        plan = json.loads(plan_text)
        return plan.get("steps", [])
        
    except Exception as e:
        print(f"Error creating execution plan: {e}")
        
        # Fallback: Tạo plan đơn giản nếu LLM gặp lỗi
        return [
            {
                "step_number": 1,
                "description": "Truy vấn dữ liệu từ database",
                "sql_needed": True,
                "chart_needed": complexity["needs_chart"]
            }
        ]


def plan_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Planner - Phân tích và lên kế hoạch cho câu hỏi.
    
    Đây là node đầu tiên trong workflow, thực hiện:
    1. Phát hiện độ phức tạp của câu hỏi
    2. Xác định có cần vẽ biểu đồ không
    3. Tạo execution plan nếu là câu hỏi phức tạp
    
    Args:
        state: Dictionary chứa trạng thái workflow, cần có key "question"
        
    Returns:
        State mới với các key bổ sung:
        - complexity: Dict chứa thông tin độ phức tạp
        - execution_plan: List các bước thực thi (nếu multi-step)
        - needs_chart: Boolean - có cần vẽ biểu đồ
        - chart_type: String - loại biểu đồ (nếu cần)
    """
    question = state.get("question", "")
    
    # Bước 1: Phát hiện độ phức tạp
    complexity = detect_query_complexity(question)
    
    # Bước 2: Tạo execution plan cho câu hỏi phức tạp
    if complexity["is_multi_step"]:
        execution_plan = create_execution_plan(question, complexity)
    else:
        execution_plan = []
    
    # Trả về state mới với thông tin đã phân tích
    return {
        **state,
        "complexity": complexity,
        "execution_plan": execution_plan,
        "needs_chart": complexity["needs_chart"],
        "chart_type": complexity.get("chart_type"),
    }
