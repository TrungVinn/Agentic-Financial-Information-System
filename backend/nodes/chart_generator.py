from typing import Dict, Any, Optional, List
import json
import os

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import psycopg2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from google import generativeai as google_genai

from config import DB_CONNECTION_STRING
from nodes.utils import (
    extract_ticker,
    extract_date_range,
    extract_date_parts,
    normalize_text,
)

load_dotenv()
if os.getenv("GOOGLE_API_KEY") in (None, "") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def _required_columns_for_chart(chart_type: Optional[str]) -> List[str]:
    mapping = {
        "candlestick": ["date", "open", "high", "low", "close", "volume"],
        "volume": ["date", "open", "close", "volume"],
        "comparison": ["date", "ticker", "close"],
    }
    return mapping.get(chart_type, ["date", "close", "volume"])


def _prepare_data_preview(df: pd.DataFrame, max_rows: int = 60) -> List[Dict[str, Any]]:
    """Chuẩn bị preview của DataFrame để gửi cho LLM, convert tất cả Timestamp và các kiểu không JSON serializable."""
    preview = df.head(max_rows).copy()
    for col in preview.columns:
        # Convert datetime/Timestamp sang string
        if pd.api.types.is_datetime64_any_dtype(preview[col]):
            preview[col] = preview[col].dt.strftime("%Y-%m-%d")
        # Convert các giá trị Timestamp lẻ (nếu có)
        elif preview[col].dtype == "object":
            # Kiểm tra nếu có Timestamp objects
            preview[col] = preview[col].apply(
                lambda x: x.strftime("%Y-%m-%d") if isinstance(x, pd.Timestamp) else x
            )
        # Convert NaN/None thành None (JSON serializable)
        preview[col] = preview[col].where(pd.notna(preview[col]), None)

    # Convert sang dict và xử lý các giá trị không serializable
    records = preview.to_dict(orient="records")
    # Đảm bảo tất cả giá trị đều JSON serializable
    for record in records:
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.strftime("%Y-%m-%d")
            elif pd.isna(value):
                record[key] = None
            elif isinstance(value, (np.integer, np.floating)):
                record[key] = (
                    float(value) if isinstance(value, np.floating) else int(value)
                )
    return records


def build_chart_sql(
    question: str,
    chart_type: Optional[str],
    chart_request: Optional[Dict[str, Any]],
    ticker: Optional[str],
) -> Optional[str]:
    """
    Sinh SQL bằng LLM để lấy dữ liệu vẽ biểu đồ.
    Trả về None nếu không thể sinh được.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    google_genai.configure(api_key=api_key)
    required_cols = ", ".join(_required_columns_for_chart(chart_type))
    chart_request_json = json.dumps(chart_request or {}, ensure_ascii=False)
    ticker_hint = ticker or "unknown"

    # Schema
    schema = (
        "=== DATASET SCHEMA ===\n"
        "Table: prices\n"
        "  Columns: date (TEXT, YYYY-MM-DD), open, high, low, close, volume, dividends, stock_splits, ticker\n"
        "  Note: prices.ticker joins with companies.symbol\n\n"
        "Table: companies\n"
        "  Columns: symbol (TEXT, primary key), name, sector, industry, market_cap, pe_ratio, ...\n"
        "  Note: companies.symbol is the primary key\n\n"
        "⚠️ KHÔNG tồn tại bảng 'stock_prices'. CHỈ dùng 'prices' và 'companies'.\n\n"
    )

    # Constraints
    constraints = (
        "=== QUY TẮC QUAN TRỌNG CHO VISUALIZATION ===\n"
        "1. Khi câu hỏi yêu cầu 'per company', 'each company', 'for each DJIA company':\n"
        "   → PHẢI GROUP BY ticker hoặc symbol (KHÔNG BAO GIỜ GROUP BY date)\n"
        "   → Mỗi dòng kết quả = một công ty\n\n"
        "2. Nếu câu hỏi liên quan đến toàn năm (in 2024, during 2024):\n"
        "   → Phải aggregate toàn bộ năm (AVG, SUM, COUNT cho cả năm)\n"
        "   → KHÔNG GROUP BY date (trừ khi user nói rõ 'per day')\n\n"
        "3. Scatter plot/correlation chart:\n"
        "   → Mỗi điểm = một company → GROUP BY ticker\n"
        "   → Trừ khi user nói 'per day' → GROUP BY date\n\n"
        "4. Bar chart:\n"
        "   → Một bar = một entity duy nhất (company hoặc day)\n"
        "   → Nếu 'per company' → GROUP BY ticker\n\n"
        "5. Pie chart:\n"
        "   → Một slice = một category (sector, industry...)\n"
        "   → GROUP BY category đó (sector, industry...)\n\n"
        "6. Không được include columns không trong GROUP BY trừ khi chúng được aggregate.\n\n"
    )

    # Examples
    examples = (
        "=== VÍ DỤ ĐÚNG (Few-shot Examples) ===\n\n"
        "Example 1: Scatter plot market cap vs P/E for all companies\n"
        "SQL: SELECT symbol, name, market_cap, pe_ratio FROM companies;\n\n"
        "Example 2: Pie chart distribution by sector\n"
        "SQL: SELECT sector, COUNT(*) as count FROM companies GROUP BY sector;\n\n"
        "Example 3: Bar chart total dividends per company in 2024\n"
        "SQL: SELECT p.ticker, c.name, SUM(p.dividends) as total_dividends FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE strftime('%Y', p.date) = '2024' GROUP BY p.ticker;\n\n"
        "Example 4: Scatter plot average volume vs average price per company in 2024\n"
        "SQL: SELECT p.ticker, c.name, AVG(p.volume) as avg_volume, AVG(p.close) as avg_close FROM prices p JOIN companies c ON p.ticker = c.symbol WHERE strftime('%Y', p.date) = '2024' GROUP BY p.ticker;\n\n"
        "❌ SAI: GROUP BY date khi câu hỏi về 'per company'\n"
        "❌ SAI: Không GROUP BY khi cần aggregate per company\n\n"
    )

    system_prompt = (
        "Bạn là trợ lý SQL cho PostgreSQL nhằm chuẩn bị dữ liệu vẽ biểu đồ tài chính.\n"
        "Luôn trả về một câu SELECT thuần, không markdown, không comment, không giải thích.\n"
    )

    guidance = (
        "=== QUY TẮC CHUNG ===\n"
        "- CHỈ sử dụng bảng prices và companies.\n"
        "- Nếu biết ticker, dùng WHERE prices.ticker = :ticker.\n"
        "- Nếu có khoảng ngày, dùng date(date) BETWEEN date(:start_date) AND date(:end_date).\n"
        "- Nếu không có khoảng ngày, dùng CTE với LIMIT :window_days (ví dụ 180) cho dữ liệu gần nhất.\n"
        "- Luôn ORDER BY date ASC (trừ khi GROUP BY ticker).\n"
        "- Đối với comparison, phải trả về cột ticker và ít nhất hai công ty.\n"
        "- Khi câu hỏi về 'all DJIA companies', 'each DJIA company', 'all companies':\n"
        "  * PHẢI JOIN companies với prices: JOIN companies ON prices.ticker = companies.symbol\n"
        "  * Trả về các cột: ticker (hoặc symbol), name (từ companies), sector, market_cap, pe_ratio, và các metrics từ prices\n"
        "  * Nếu cần aggregate (avg, sum, count): dùng GROUP BY ticker hoặc symbol\n"
        "- Không được tạo bảng mới hay sử dụng tên bảng khác.\n"
        "- Không dùng comment hoặc nhiều câu SQL.\n"
    )

    prompt = (
        f"{system_prompt}\n\n"
        f"{schema}\n"
        f"{constraints}\n"
        f"{examples}\n"
        f"{guidance}\n\n"
        f"=== THÔNG TIN CÂU HỎI ===\n"
        f"Câu hỏi: {question}\n"
        f"Loại biểu đồ (gợi ý): {chart_type or 'auto'}\n"
        f"Yêu cầu chart JSON: {chart_request_json}\n"
        f"Ticker chính (nếu có): {ticker_hint}\n"
        f"Cần tối thiểu các cột: {required_cols}\n\n"
        f"SQL:"
    )

    try:
        model = google_genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        sql = (resp.text or "").strip()

        if sql.startswith("```"):
            lines = sql.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = "\n".join(lines).strip()

        if sql and not sql.endswith(";"):
            sql += ";"

        return sql or None
    except Exception as e:
        print(f"Error generating chart SQL with LLM: {e}")
        return None


def build_chart_code(
    question: str,
    chart_type_hint: Optional[str],
    chart_request: Optional[Dict[str, Any]],
    df: pd.DataFrame,
) -> Optional[str]:
    """
    Yêu cầu LLM sinh code Plotly để dựng biểu đồ trực tiếp từ DataFrame df.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key or df is None or df.empty:
        return None

    google_genai.configure(api_key=api_key)
    preview = _prepare_data_preview(df)
    columns = ", ".join(df.columns.tolist())
    chart_request_json = json.dumps(chart_request or {}, ensure_ascii=False)

    # Tạo data_json với error handling
    try:
        data_json = json.dumps(preview, ensure_ascii=False, default=str)
    except Exception as e:
        # Nếu vẫn lỗi, thử convert lại tất cả giá trị
        print(f"Warning: Error serializing preview data: {e}")
        # Convert tất cả giá trị không serializable sang string
        safe_preview = []
        for record in preview:
            safe_record = {}
            for key, value in record.items():
                try:
                    json.dumps(value)  # Test serialization
                    safe_record[key] = value
                except (TypeError, ValueError):
                    safe_record[key] = str(value) if value is not None else None
            safe_preview.append(safe_record)
        data_json = json.dumps(safe_preview, ensure_ascii=False)

    system_prompt = (
        "Bạn là trợ lý dựng biểu đồ Plotly bằng Python. "
        "Hãy đọc câu hỏi và dữ liệu mẫu, sau đó sinh code Python (không markdown) tạo đối tượng Plotly Figure."
    )

    # Constraints cho visualization
    constraints = (
        "=== QUY TẮC QUAN TRỌNG ===\n"
        "1. Khi câu hỏi về 'per company', 'each company', 'for each DJIA company':\n"
        "   → Mỗi điểm/bar/slice = một công ty\n"
        "   → Nếu df chưa được groupby theo ticker/symbol, PHẢI dùng df.groupby('ticker') hoặc df.groupby('symbol')\n"
        "   → KHÔNG groupby theo date khi câu hỏi về per company\n\n"
        "2. Scatter plot:\n"
        "   → Mỗi điểm = một company (nếu 'per company')\n"
        "   → Dùng go.Scatter hoặc px.scatter với x và y từ df\n"
        "   → Thêm text=name hoặc text=ticker để hiển thị nhãn công ty\n\n"
        "3. Bar chart:\n"
        "   → Một bar = một entity (company hoặc day)\n"
        "   → Nếu 'per company' → x=ticker/name, y=metric\n"
        "   → Có thể sort theo y: df = df.sort_values('metric', ascending=False)\n\n"
        "4. Pie chart:\n"
        "   → Một slice = một category (sector, industry...)\n"
        "   → Nếu df có cột sector và market_cap (hoặc metric khác): dùng trực tiếp df, không cần groupby lại\n"
        "   → Nếu df chưa được aggregate và cần count: df = df.groupby('sector').size().reset_index(name='count')\n"
        "   → labels=category_column (sector/industry), values=metric_column (market_cap/sum/count)\n"
        "   → Dùng go.Pie hoặc px.pie\n\n"
        "5. Time series line chart:\n"
        "   → Khi câu hỏi về 'time series', 'over time', 'from ... to ...', 'during ...', 'closing price over time':\n"
        "   → Dùng go.Scatter với mode='lines' (KHÔNG phải 'markers')\n"
        "   → x=df['date'], y=df['close'] (hoặc cột giá khác như 'open', 'high', 'low')\n"
        "   → Đảm bảo cột date đã là datetime (thường đã được xử lý)\n"
        "   → Thêm hovertemplate để hiển thị thông tin khi hover\n"
        "   → Format ngày trên trục x: figure.update_xaxes(tickformat='%Y-%m-%d')\n\n"
        "6. BẮT BUỘC sử dụng DataFrame df có sẵn, KHÔNG hard-code dữ liệu.\n"
        "7. Code phải gán kết quả vào biến 'figure' (go.Figure).\n"
        "8. Không in/log, không markdown, không tiền tố 'python'.\n\n"
    )

    # Few-shot examples
    examples = (
        "=== VÍ DỤ ĐÚNG (Few-shot Examples) ===\n\n"
        "Example 1: Scatter plot market cap vs P/E for all companies\n"
        "DataFrame có: symbol, name, market_cap, pe_ratio\n"
        "Code:\n"
        "figure = go.Figure()\n"
        "figure.add_trace(go.Scatter(\n"
        "    x=df['market_cap'],\n"
        "    y=df['pe_ratio'],\n"
        "    mode='markers+text',\n"
        "    text=df['name'],\n"
        "    textposition='top center',\n"
        "    name='Companies'\n"
        "))\n"
        "figure.update_layout(title='Market Cap vs P/E Ratio', xaxis_title='Market Cap', yaxis_title='P/E Ratio')\n\n"
        "Example 2: Pie chart distribution by sector (count)\n"
        "DataFrame có: sector (có thể lặp lại)\n"
        "Code:\n"
        "sector_counts = df.groupby('sector').size().reset_index(name='count')\n"
        "figure = go.Figure(data=[go.Pie(labels=sector_counts['sector'], values=sector_counts['count'])])\n"
        "figure.update_layout(title='Distribution by Sector')\n\n"
        "Example 2b: Pie chart market cap proportions by sector\n"
        "DataFrame có: sector, và một cột chứa tổng market_cap (ví dụ: 'SUM(c.market_cap)' hoặc tên khác)\n"
        "Code:\n"
        "# Xác định tên cột market_cap từ df.columns (thường chứa 'market' hoặc 'sum')\n"
        "# Nếu không chắc, dùng df.columns[1] (cột thứ 2) hoặc kiểm tra df.columns\n"
        "value_col = [col for col in df.columns if col != 'sector'][0]  # Lấy cột đầu tiên không phải sector\n"
        "figure = go.Figure(data=[go.Pie(labels=df['sector'], values=df[value_col], textinfo='label+percent')])\n"
        "figure.update_layout(title='Market Capitalization Proportions by Sector')\n\n"
        "Example 2c: Bar chart market cap by sector\n"
        "DataFrame có: sector, và một cột chứa tổng market_cap\n"
        "Code:\n"
        "# Xác định tên cột market_cap\n"
        "value_col = [col for col in df.columns if col != 'sector'][0]  # Lấy cột đầu tiên không phải sector\n"
        "df_sorted = df.sort_values(value_col, ascending=False)\n"
        "figure = go.Figure(data=[go.Bar(x=df_sorted['sector'], y=df_sorted[value_col])])\n"
        "figure.update_layout(title='Market Capitalization by Sector', xaxis_title='Sector', yaxis_title='Market Cap')\n\n"
        "Example 3: Bar chart total dividends per company in 2024\n"
        "DataFrame có: ticker, name, total_dividends\n"
        "Code:\n"
        "df_sorted = df.sort_values('total_dividends', ascending=False)\n"
        "figure = go.Figure(data=[go.Bar(x=df_sorted['name'], y=df_sorted['total_dividends'])])\n"
        "figure.update_layout(title='Total Dividends per Company in 2024', xaxis_title='Company', yaxis_title='Total Dividends')\n\n"
        "Example 3b: Bar chart top 10 companies by market cap\n"
        "DataFrame có: symbol (hoặc ticker), name, market_cap (đã được ORDER BY market_cap DESC LIMIT 10)\n"
        "Code:\n"
        "# DataFrame đã được sort, chỉ cần vẽ\n"
        "figure = go.Figure(data=[go.Bar(x=df['name'], y=df['market_cap'])])\n"
        "figure.update_layout(title='Top 10 Companies by Market Capitalization', xaxis_title='Company', yaxis_title='Market Cap', xaxis_tickangle=-45)\n\n"
        "Example 4: Scatter plot average volume vs average price per company\n"
        "DataFrame có: ticker, name, avg_volume, avg_close\n"
        "Code:\n"
        "figure = go.Figure()\n"
        "figure.add_trace(go.Scatter(\n"
        "    x=df['avg_volume'],\n"
        "    y=df['avg_close'],\n"
        "    mode='markers+text',\n"
        "    text=df['name'],\n"
        "    textposition='top center',\n"
        "    name='Companies'\n"
        "))\n"
        "figure.update_layout(title='Average Volume vs Average Price', xaxis_title='Avg Volume', yaxis_title='Avg Price')\n\n"
        "Example 5: Time series line chart of closing price\n"
        "DataFrame có: date, close, volume (cột date đã là datetime)\n"
        "Code:\n"
        "figure = go.Figure()\n"
        "figure.add_trace(go.Scatter(\n"
        "    x=df['date'],\n"
        "    y=df['close'],\n"
        "    mode='lines',\n"
        "    name='Close Price',\n"
        "    line=dict(color='#2E86AB', width=2),\n"
        "    hovertemplate='Date: %{x|%Y-%m-%d}<br>Close: $%{y:.2f}<extra></extra>'\n"
        "))\n"
        "figure.update_layout(\n"
        "    title='Closing Price Over Time',\n"
        "    xaxis_title='Date',\n"
        "    yaxis_title='Price ($)',\n"
        "    hovermode='x unified',\n"
        "    xaxis=dict(tickformat='%Y-%m-%d')\n"
        ")\n\n"
        "❌ SAI: Không groupby khi cần aggregate per company\n"
        "❌ SAI: Groupby theo date khi câu hỏi về per company\n"
        "❌ SAI: Hard-code dữ liệu thay vì dùng df\n"
        "❌ SAI: Dùng mode='markers' thay vì mode='lines' cho time series\n\n"
    )

    guidance = (
        "=== YÊU CẦU KỸ THUẬT ===\n"
        "- DataFrame có tên là df (pandas DataFrame). Có thể sử dụng: pd, np, go, px, make_subplots.\n"
        "- TÊN CỘT ĐÃ ĐƯỢC NORMALIZE VỀ LOWERCASE: date, close, open, high, low, volume, ticker, symbol, name, sector, market_cap, ...\n"
        "- Code phải gán kết quả cuối cùng vào biến 'figure' kiểu plotly.graph_objects.Figure.\n"
        "- Nếu cần transform (groupby, pivot, tính toán…), hãy thực hiện trong code.\n"
        "- Tự động suy luận loại biểu đồ phù hợp nếu câu hỏi không rõ.\n"
        "- BẮT BUỘC sử dụng chính DataFrame df; không tái tạo dữ liệu thủ công.\n"
        "- Không in/log, không viết markdown, không thêm tiền tố như 'python'. Chỉ trả về code Python thuần.\n"
        "- Với comparison nhiều ticker, lọc/loop theo ticker. Với correlation heatmap, tạo ma trận tương quan.\n"
        "- Giữ số trace vừa phải (≤5). Đặt tiêu đề, nhãn trục rõ ràng. Dùng format ngày chuẩn nếu trục x là thời gian.\n"
        "- QUAN TRỌNG: Khi DataFrame có cột với tên phức tạp (ví dụ 'sum(c.market_cap)'), hãy:\n"
        "  * Sử dụng tên cột chính xác từ df.columns (đã lowercase)\n"
        "  * Hoặc dùng df.columns[0], df.columns[1]... để tham chiếu theo vị trí\n"
        "  * Hoặc tìm cột bằng cách: [col for col in df.columns if 'keyword' in col.lower()][0]\n"
        "- Với pie/bar chart về sector: nếu df có cột 'sector' và một cột metric (market_cap, count...), dùng trực tiếp các cột đó.\n"
        "- Với time series: cột 'date' đã là datetime, dùng trực tiếp df['date'] và df['close'] (hoặc open/high/low).\n"
    )

    prompt = (
        f"{system_prompt}\n\n"
        f"{constraints}\n"
        f"{examples}\n"
        f"{guidance}\n\n"
        f"=== THÔNG TIN CÂU HỎI VÀ DỮ LIỆU ===\n"
        f"Câu hỏi: {question}\n"
        f"Chart type hint: {chart_type_hint or 'auto'}\n"
        f"Chart request JSON: {chart_request_json}\n"
        f"Các cột sẵn có trong df: {columns}\n"
        f"Dữ liệu mẫu (JSON, {len(preview)} dòng đầu):\n{data_json}\n\n"
        f"Hãy sinh code Python để tạo biểu đồ Plotly phù hợp với câu hỏi và dữ liệu trên."
    )

    try:
        model = google_genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        code = (resp.text or "").strip()
        if code.startswith("```"):
            parts = code.split("```")
            code = parts[1] if len(parts) > 1 else code
        return code.strip()
    except Exception as e:
        print(f"Error generating chart code with LLM: {e}")
        return None


def render_chart_from_code(
    code: Optional[str], df: pd.DataFrame
) -> Optional[go.Figure]:
    if not code:
        return None
    code = code.strip()
    if code.lower().startswith("python"):
        newline_idx = code.find("\n")
        code = code[newline_idx + 1 :] if newline_idx != -1 else ""
    local_env: Dict[str, Any] = {
        "pd": pd,
        "np": np,
        "go": go,
        "px": px,
        "make_subplots": make_subplots,
        "df": df.copy(),
    }
    try:
        exec(code, {}, local_env)
    except Exception as e:
        print(f"Error executing chart code: {e}\nCode:\n{code}")
        return None

    figure = local_env.get("figure")
    if isinstance(figure, go.Figure):
        return figure

    build_fn = local_env.get("build_chart")
    if callable(build_fn):
        try:
            figure = build_fn(df.copy())
            if isinstance(figure, go.Figure):
                return figure
        except Exception as e:
            print(f"Error calling build_chart(): {e}")

    for value in local_env.values():
        if isinstance(value, go.Figure):
            return value

    print("LLM code did not produce a Plotly Figure.")
    return None


def create_line_chart(df: pd.DataFrame, ticker: str, title: str = None) -> go.Figure:
    """Tạo biểu đồ đường cho giá cổ phiếu."""
    if df.empty:
        return None

    fig = go.Figure()

    # Thêm đường giá đóng cửa
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="Close Price",
            line=dict(color="#2E86AB", width=2),
            hovertemplate="Date: %{x}<br>Close: $%{y:.2f}<extra></extra>",
        )
    )

    # Thêm moving average 20 ngày nếu có đủ dữ liệu
    if len(df) >= 20:
        df["ma20"] = df["close"].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["ma20"],
                mode="lines",
                name="MA 20",
                line=dict(color="#F77F00", width=1, dash="dash"),
                hovertemplate="Date: %{x}<br>MA20: $%{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=title or f"{ticker} - Biểu đồ giá",
        xaxis_title="Ngày",
        yaxis_title="Giá ($)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_candlestick_chart(
    df: pd.DataFrame, ticker: str, title: str = None
) -> go.Figure:
    """Tạo biểu đồ nến cho giá cổ phiếu."""
    if df.empty or not all(
        col in df.columns for col in ["open", "high", "low", "close"]
    ):
        return None

    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title or f"{ticker} - Biểu đồ nến", "Khối lượng giao dịch"),
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
            increasing_line_color="#26A69A",
            decreasing_line_color="#EF5350",
        ),
        row=1,
        col=1,
    )

    # Volume bar chart
    colors = [
        "#26A69A" if close >= open else "#EF5350"
        for close, open in zip(df["close"], df["open"])
    ]

    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["volume"],
            name="Volume",
            marker_color=colors,
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=700,
        showlegend=True,
        hovermode="x unified",
    )

    fig.update_xaxes(title_text="Ngày", row=2, col=1)
    fig.update_yaxes(title_text="Giá ($)", row=1, col=1)
    fig.update_yaxes(title_text="Khối lượng", row=2, col=1)

    return fig


def create_comparison_chart(
    df: pd.DataFrame, tickers: list, title: str = None
) -> go.Figure:
    """Tạo biểu đồ so sánh nhiều cổ phiếu."""
    if df.empty or "ticker" not in df.columns:
        return None

    fig = go.Figure()

    colors = ["#2E86AB", "#F77F00", "#06A77D", "#D62828", "#F4A259", "#4059AD"]

    for i, ticker in enumerate(tickers):
        ticker_df = df[df["ticker"] == ticker].copy()
        if not ticker_df.empty:
            # Normalize to percentage change from first value
            first_close = ticker_df["close"].iloc[0]
            ticker_df["pct_change"] = (
                (ticker_df["close"] - first_close) / first_close
            ) * 100

            fig.add_trace(
                go.Scatter(
                    x=ticker_df["date"],
                    y=ticker_df["pct_change"],
                    mode="lines",
                    name=ticker,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f"{ticker}<br>Date: %{{x}}<br>Change: %{{y:.2f}}%<extra></extra>",
                )
            )

    fig.update_layout(
        title=title or "So sánh biến động giá (%)",
        xaxis_title="Ngày",
        yaxis_title="Thay đổi (%)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    return fig


def create_volume_chart(df: pd.DataFrame, ticker: str, title: str = None) -> go.Figure:
    """Tạo biểu đồ khối lượng giao dịch."""
    if df.empty or "volume" not in df.columns:
        return None

    fig = go.Figure()

    colors = [
        "#26A69A" if close >= open else "#EF5350"
        for close, open in zip(df["close"], df["open"])
    ]

    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["volume"],
            name="Volume",
            marker_color=colors,
            hovertemplate="Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>",
        )
    )

    # Add moving average of volume
    if len(df) >= 20:
        df["vol_ma20"] = df["volume"].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["vol_ma20"],
                mode="lines",
                name="Volume MA 20",
                line=dict(color="#F77F00", width=2),
                hovertemplate="Date: %{x}<br>Vol MA20: %{y:,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=title or f"{ticker} - Khối lượng giao dịch",
        xaxis_title="Ngày",
        yaxis_title="Khối lượng",
        hovermode="x unified",
        template="plotly_white",
        height=400,
        showlegend=True,
    )

    return fig


def fetch_chart_data(question: str, ticker: str, chart_type: str) -> pd.DataFrame:
    """Lấy dữ liệu từ database để vẽ biểu đồ."""
    engine = create_engine(DB_CONNECTION_STRING)

    try:
        # Xác định khoảng thời gian
        start_date, end_date = extract_date_range(question)
        date_parts = extract_date_parts(question)

        # Xây dựng SQL query (PostgreSQL syntax)
        if chart_type == "comparison":
            # So sánh nhiều công ty - cần tìm tất cả tickers trong câu hỏi
            # Fallback: lấy tất cả công ty trong 1 tháng gần nhất
            sql = """
                SELECT date, ticker, open, high, low, close, volume
                FROM prices
                WHERE date >= CURRENT_DATE - INTERVAL '1 month'
                ORDER BY date ASC, ticker ASC
            """
        else:
            # Single ticker
            where_clauses = [f"ticker = '{ticker}'"]

            if start_date and end_date:
                where_clauses.append(
                    f"date BETWEEN '{start_date}'::date AND '{end_date}'::date"
                )
            elif "year" in date_parts:
                where_clauses.append(f"EXTRACT(YEAR FROM date) = {date_parts['year']}")
            elif "month" in date_parts and "year" in date_parts:
                where_clauses.append(
                    f"EXTRACT(YEAR FROM date) = {date_parts['year']} AND EXTRACT(MONTH FROM date) = {date_parts['month']}"
                )
            else:
                # Default: last 3 months
                where_clauses.append("date >= CURRENT_DATE - INTERVAL '3 months'")

            where_clause = " AND ".join(where_clauses)

            sql = f"""
                SELECT date, open, high, low, close, volume
                FROM prices
                WHERE {where_clause}
                ORDER BY date ASC
            """

        with engine.connect() as conn:
            df = pd.read_sql_query(text(sql), conn)

        # Convert date to datetime (PostgreSQL trả về date object)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        return df
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        import traceback

        traceback.print_exc()
        return pd.DataFrame()
    finally:
        engine.dispose()


def generate_chart(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node tạo biểu đồ dựa trên yêu cầu."""
    question = state.get("question", "")
    ticker = state.get("ticker")
    needs_chart = state.get("needs_chart", False)
    chart_type = state.get("chart_type", "line")
    chart_request = state.get("chart_request")
    df = state.get("df")

    if not needs_chart:
        return {**state, "chart": None}

    # Kiểm tra nếu câu hỏi về tất cả DJIA companies, top N companies, hoặc sector/industry
    q = normalize_text(question)
    is_all_companies = any(
        phrase in q
        for phrase in [
            "all companies",
            "all djia",
            "each company",
            "each djia company",
            "tất cả công ty",
            "mỗi công ty",
            "for all djia",
            "for each djia",
            "top ",
            "top companies",
            "top 10",
            "top 5",
            "top 20",  # Top N companies
            "largest companies",
            "biggest companies",
            "highest companies",
        ]
    )
    is_sector_query = any(
        word in q for word in ["sector", "industry", "ngành", "lĩnh vực"]
    )

    # Nếu không có ticker, thử trích xuất (trừ khi là all companies hoặc sector query)
    if not ticker and not is_all_companies and not is_sector_query:
        ticker = extract_ticker(question)

    # Nếu vẫn không có ticker và không phải all companies/sector, không vẽ được
    if (
        not ticker
        and chart_type != "comparison"
        and not is_all_companies
        and not is_sector_query
    ):
        return {
            **state,
            "chart": None,
            "chart_error": "Không xác định được mã cổ phiếu",
        }

    # Nếu đã có df từ SQL execution, dùng luôn (không fetch lại)
    # Với all companies hoặc sector query, SQL đã trả về đúng dữ liệu
    if not is_all_companies and not is_sector_query:
        if df is None or df.empty or "date" not in df.columns:
            df = fetch_chart_data(question, ticker, chart_type)

    if df is None or df.empty:
        return {**state, "chart": None, "chart_error": "Không có dữ liệu để vẽ biểu đồ"}

    # Normalize column names to lowercase để tránh vấn đề case sensitivity
    df.columns = [col.lower() for col in df.columns]

    # Ensure date column is datetime (nếu có)
    if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    chart = None
    error_msg = None
    try:
        code = build_chart_code(question, chart_type, chart_request, df)
        if not code:
            error_msg = "LLM không thể sinh code Python để vẽ biểu đồ."
        else:
            chart = render_chart_from_code(code, df)
            if chart is None:
                error_msg = f"Code Python được sinh ra không tạo được biểu đồ Plotly hợp lệ. Code:\n{code[:500]}..."
    except Exception as e:
        error_msg = f"Lỗi khi sinh/thực thi code biểu đồ: {str(e)}"
        print(f"Error generating chart code via LLM: {e}")

    if chart is None:
        return {
            **state,
            "chart": None,
            "chart_error": error_msg
            or "Không thể tạo biểu đồ từ mô tả của bạn. Hãy cụ thể hơn hoặc thử lại.",
        }

    return {**state, "chart": chart, "chart_error": None}
