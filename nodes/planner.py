from typing import Dict, Any, Optional, List
import os
import re
from google import genai as google_genai
from dotenv import load_dotenv
from nodes.utils import normalize_text, extract_ticker

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def detect_query_complexity(question: str) -> Dict[str, Any]:
    """Phân tích câu hỏi để xác định độ phức tạp và yêu cầu."""
    q = normalize_text(question)
    
    complexity = {
        "is_multi_step": False,
        "needs_chart": False,
        "chart_type": None,
        "is_comparison": False,
        "is_aggregation": False,
        "is_statistical": False,
        "time_series": False,
        "involves_multiple_companies": False,
    }
    
    # Kiểm tra các từ khóa yêu cầu vẽ biểu đồ
    chart_keywords = [
        "vẽ", "ve", "draw", "plot", "chart", "graph", "biểu đồ", "bieu do",
        "visualize", "show trend", "hiển thị xu hướng", "hien thi xu huong"
    ]
    
    if any(keyword in q for keyword in chart_keywords):
        complexity["needs_chart"] = True
        
        # Xác định loại biểu đồ
        if any(word in q for word in ["candlestick", "nến", "nen", "ohlc"]):
            complexity["chart_type"] = "candlestick"
        elif any(word in q for word in ["volume", "khối lượng", "khoi luong"]):
            complexity["chart_type"] = "volume"
        elif any(word in q for word in ["compare", "so sánh", "so sanh", "comparison"]):
            complexity["chart_type"] = "comparison"
        else:
            complexity["chart_type"] = "line"
    
    # Kiểm tra câu hỏi về xu hướng giá
    trend_keywords = ["trend", "xu hướng", "xu huong", "thay đổi", "thay doi", "biến động", "bien dong"]
    if any(keyword in q for keyword in trend_keywords) and not complexity["needs_chart"]:
        complexity["needs_chart"] = True
        complexity["chart_type"] = "line"
    
    # Kiểm tra so sánh
    comparison_keywords = ["compare", "so sánh", "so sanh", "vs", "versus", "higher", "lower", 
                          "cao hơn", "cao hon", "thấp hơn", "thap hon", "which company"]
    if any(keyword in q for keyword in comparison_keywords):
        complexity["is_comparison"] = True
    
    # Kiểm tra tổng hợp
    aggregation_keywords = ["average", "total", "sum", "trung bình", "trung binh", "tổng", "tong",
                           "median", "mean", "max", "min", "highest", "lowest"]
    if any(keyword in q for keyword in aggregation_keywords):
        complexity["is_aggregation"] = True
    
    # Kiểm tra phân tích thống kê
    statistical_keywords = ["correlation", "volatility", "standard deviation", "beta", "sharpe ratio",
                           "tương quan", "tuong quan", "biến động", "bien dong", "độ lệch chuẩn"]
    if any(keyword in q for keyword in statistical_keywords):
        complexity["is_statistical"] = True
        complexity["is_multi_step"] = True
    
    # Kiểm tra time series
    time_keywords = ["over time", "theo thời gian", "theo thoi gian", "from .* to", 
                    "trong khoảng", "trong khoang", "during", "between"]
    if any(re.search(keyword, q) for keyword in time_keywords):
        complexity["time_series"] = True
    
    # Kiểm tra multi-company
    if "all companies" in q or "tất cả công ty" in q or "tat ca cong ty" in q:
        complexity["involves_multiple_companies"] = True
        complexity["is_multi_step"] = True
    
    # Xác định multi-step query
    multi_step_indicators = [
        complexity["is_statistical"],
        complexity["involves_multiple_companies"],
        (complexity["is_comparison"] and complexity["is_aggregation"]),
    ]
    
    if any(multi_step_indicators):
        complexity["is_multi_step"] = True
    
    return complexity


def create_execution_plan(question: str, complexity: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tạo kế hoạch thực thi cho các câu hỏi phức tạp."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = google_genai.Client(api_key=api_key)
    
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
        resp = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
        )
        
        # Parse JSON response
        import json
        plan_text = resp.text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in plan_text:
            plan_text = plan_text.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_text:
            plan_text = plan_text.split("```")[1].split("```")[0].strip()
        
        plan = json.loads(plan_text)
        return plan.get("steps", [])
    except Exception as e:
        print(f"Error creating execution plan: {e}")
        # Fallback: tạo plan đơn giản
        return [
            {
                "step_number": 1,
                "description": "Truy vấn dữ liệu",
                "sql_needed": True,
                "chart_needed": complexity["needs_chart"]
            }
        ]


def plan_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node planner - phân tích và lên kế hoạch cho câu hỏi."""
    question = state.get("question", "")
    
    # Phát hiện độ phức tạp
    complexity = detect_query_complexity(question)
    
    # Tạo execution plan cho câu hỏi phức tạp
    if complexity["is_multi_step"]:
        execution_plan = create_execution_plan(question, complexity)
    else:
        execution_plan = []
    
    return {
        **state,
        "complexity": complexity,
        "execution_plan": execution_plan,
        "needs_chart": complexity["needs_chart"],
        "chart_type": complexity.get("chart_type"),
    }
