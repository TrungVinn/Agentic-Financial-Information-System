"""
Query Planner Node - Phân tích độ phức tạp của câu hỏi.

Module này là bước đầu tiên trong workflow, phân tích câu hỏi người dùng để:
1. Phân loại câu hỏi (so sánh, tổng hợp, thống kê...)
2. Phát hiện yêu cầu vẽ biểu đồ và loại biểu đồ
"""

from typing import Dict, Any, Optional, List
import os
import re
import json
from nodes.utils import normalize_text, extract_ticker


def detect_query_complexity(question: str, force_chart: bool = False) -> Dict[str, Any]:
    """
    Phân tích câu hỏi để xác định độ phức tạp và yêu cầu.

    Args:
        question: Câu hỏi từ người dùng (tiếng Việt hoặc tiếng Anh)

    Returns:
        Dictionary chứa các thông tin:
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
        "needs_chart": False,  # Cần vẽ biểu đồ
        "chart_type": None,  # Loại biểu đồ (nếu cần)
        "is_comparison": False,  # Câu hỏi so sánh
        "is_aggregation": False,  # Câu hỏi tổng hợp (avg, sum...)
        "is_statistical": False,  # Phân tích thống kê
        "time_series": False,  # Dữ liệu theo thời gian
        "involves_multiple_companies": False,  # Liên quan nhiều công ty
    }

    # ========== PHÁT HIỆN YÊU CẦU VẼ BIỂU ĐỒ ==========
    # Chỉ vẽ biểu đồ khi câu hỏi chứa từ "plot" hoặc "vẽ", hoặc khi force_chart = True
    chart_trigger_patterns = [r"\bplot\b", r"\bvẽ\b", r"\bve\b"]
    has_chart_trigger = any(re.search(pattern, q) for pattern in chart_trigger_patterns)
    has_explicit_chart_request = has_chart_trigger or force_chart

    if has_chart_trigger or force_chart:
        complexity["needs_chart"] = True

        # Xác định loại biểu đồ dựa trên từ khóa
        if any(word in q for word in ["candlestick", "nến", "nen", "ohlc"]):
            # Biểu đồ nến (Open-High-Low-Close)
            complexity["chart_type"] = "candlestick"
        elif any(word in q for word in ["bar chart", "bar", "cột", "cot", "histogram"]):
            # Biểu đồ cột (bar chart)
            complexity["chart_type"] = "bar"
        elif any(
            word in q for word in ["pie chart", "pie", "tròn", "tron", "circular"]
        ):
            # Biểu đồ tròn (pie chart)
            complexity["chart_type"] = "pie"
        elif any(
            word in q for word in ["scatter", "phân tán", "phan tan", "correlation"]
        ):
            # Biểu đồ phân tán (scatter plot)
            complexity["chart_type"] = "scatter"
        elif any(word in q for word in ["heatmap", "heat map", "ma trận", "ma tran"]):
            # Biểu đồ nhiệt (heatmap)
            complexity["chart_type"] = "heatmap"
        elif (
            any(word in q for word in ["volume", "khối lượng", "khoi luong"])
            and has_explicit_chart_request
        ):
            # Biểu đồ khối lượng giao dịch
            complexity["chart_type"] = "volume"
        elif (
            any(word in q for word in ["compare", "so sánh", "so sanh", "comparison"])
            and has_explicit_chart_request
        ):
            # Biểu đồ so sánh nhiều cổ phiếu
            complexity["chart_type"] = "comparison"
        else:
            # Mặc định: biểu đồ đường (line chart)
            complexity["chart_type"] = "line"

    # ========== PHÂN LOẠI CÂU HỎI ==========

    # 1. Kiểm tra câu hỏi SO SÁNH
    # Ví dụ: "Which company had a higher closing price?"
    comparison_keywords = [
        "compare",
        "so sánh",
        "so sanh",
        "vs",
        "versus",
        "higher",
        "lower",
        "cao hơn",
        "cao hon",
        "thấp hơn",
        "thap hon",
        "which company",
    ]
    if any(keyword in q for keyword in comparison_keywords):
        complexity["is_comparison"] = True

    # 2. Kiểm tra câu hỏi TỔNG HỢP
    # Ví dụ: "What was the average closing price?", "Total volume?"
    aggregation_keywords = [
        "average",
        "total",
        "sum",
        "trung bình",
        "trung binh",
        "tổng",
        "tong",
        "median",
        "mean",
        "max",
        "min",
        "highest",
        "lowest",
    ]
    if any(keyword in q for keyword in aggregation_keywords):
        complexity["is_aggregation"] = True

    # 3. Kiểm tra phân tích THỐNG KÊ
    # Ví dụ: "Calculate volatility", "Correlation between..."
    statistical_keywords = [
        "correlation",
        "volatility",
        "standard deviation",
        "beta",
        "sharpe ratio",
        "tương quan",
        "tuong quan",
        "biến động",
        "bien dong",
        "độ lệch chuẩn",
    ]
    if any(keyword in q for keyword in statistical_keywords):
        complexity["is_statistical"] = True

    # 4. Kiểm tra TIME SERIES
    # Ví dụ: "from January to March", "during 2024", "between..."
    time_keywords = [
        "over time",
        "theo thời gian",
        "theo thoi gian",
        "from .* to",  # regex pattern
        "trong khoảng",
        "trong khoang",
        "during",
        "between",
    ]
    if any(re.search(keyword, q) for keyword in time_keywords):
        complexity["time_series"] = True

    # 5. Kiểm tra MULTI-COMPANY queries
    # Ví dụ: "all companies", "tất cả công ty", "DJIA", "each DJIA company", "top 10 companies"
    djia_keywords = [
        "djia",
        "all companies",
        "all djia",
        "each company",
        "each djia company",
        "tất cả công ty",
        "tat ca cong ty",
        "mỗi công ty",
        "moi cong ty",
        "top ",
        "top companies",
        "top 10",
        "top 5",
        "top 20",  # Top N companies
        "largest companies",
        "biggest companies",
        "highest companies",
    ]
    if any(keyword in q for keyword in djia_keywords):
        complexity["involves_multiple_companies"] = True
    return complexity

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
    force_chart = state.get("force_chart", False)

    # Bước 1: Phát hiện độ phức tạp
    complexity = detect_query_complexity(question, force_chart=force_chart)

    # Trả về state mới với thông tin đã phân tích
    return {
        **state,
        "complexity": complexity,
        "needs_chart": complexity["needs_chart"],
        "chart_type": complexity.get("chart_type"),
    }
