from typing import Dict, Any, Optional, List
import json
import os

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sqlite3
from dotenv import load_dotenv
from google import generativeai as google_genai

from config import DB_PATH
from nodes.utils import extract_ticker, extract_date_range, extract_date_parts

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
    preview = df.head(max_rows).copy()
    for col in preview.columns:
        if pd.api.types.is_datetime64_any_dtype(preview[col]):
            preview[col] = preview[col].dt.strftime("%Y-%m-%d")
    return preview.to_dict(orient="records")


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
    
    system_prompt = (
        "Bạn là trợ lý SQL cho SQLite nhằm chuẩn bị dữ liệu vẽ biểu đồ tài chính.\n"
        "Cơ sở dữ liệu CHỈ có bảng 'prices' (schema: date, open, high, low, close, volume, dividends, stock_splits, ticker)\n"
        "và bảng 'companies' (symbol, name, ...). Không tồn tại bảng 'stock_prices'.\n"
        "Luôn trả về một câu SELECT thuần, không markdown, không comment, không giải thích.\n"
        "Kết quả bắt buộc có cột 'date' định dạng YYYY-MM-DD."
    )
    
    guidance = (
        f"- Câu hỏi: {question}\n"
        f"- Loại biểu đồ (gợi ý): {chart_type or 'auto'}\n"
        f"- Yêu cầu chart JSON: {chart_request_json}\n"
        f"- Ticker chính (nếu có): {ticker_hint}\n"
        f"- Cần tối thiểu các cột: {required_cols}\n\n"
        "Quy tắc bổ sung:\n"
        "- CHỈ sử dụng bảng prices (và companies nếu thật sự cần tên công ty).\n"
        "- Nếu biết ticker, dùng WHERE prices.ticker = :ticker.\n"
        "- Nếu có khoảng ngày, dùng date(date) BETWEEN date(:start_date) AND date(:end_date).\n"
        "- Nếu không có khoảng ngày, dùng CTE với LIMIT :window_days (ví dụ 180) cho dữ liệu gần nhất.\n"
        "- Luôn ORDER BY date ASC.\n"
        "- Đối với comparison, phải trả về cột ticker và ít nhất hai công ty.\n"
        "- Không được tạo bảng mới hay sử dụng tên bảng khác.\n"
        "- Không dùng comment hoặc nhiều câu SQL."
    )
    
    prompt = f"{system_prompt}\n\n{guidance}\n\nSQL:"
    
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
    data_json = json.dumps(preview, ensure_ascii=False)
    
    system_prompt = (
        "Bạn là trợ lý dựng biểu đồ Plotly bằng Python. "
        "Hãy đọc câu hỏi và dữ liệu mẫu, sau đó sinh code Python (không markdown) tạo đối tượng Plotly Figure."
    )
    
    guidance = (
        "Yêu cầu:\n"
        "- DataFrame có tên là df (pandas DataFrame). Có thể sử dụng pandas (pd), numpy (np), plotly.graph_objects (go), plotly.express (px), make_subplots.\n"
        "- Code phải gán kết quả cuối cùng vào biến 'figure' kiểu plotly.graph_objects.Figure.\n"
        "- Nếu cần transform (groupby, pivot, tính lợi suất, correlation…), hãy thực hiện trong code.\n"
        "- Tự động suy luận loại biểu đồ phù hợp nếu câu hỏi không rõ.\n"
        "- BẮT BUỘC sử dụng chính DataFrame df; không tái tạo dữ liệu thủ công hay hard-code danh sách điểm dữ liệu.\n"
        "- Không in/log, không viết markdown, không thêm tiền tố như 'python'. Chỉ trả về code Python thuần.\n"
        "- Với comparison nhiều ticker, lọc/loop theo ticker. Với correlation heatmap, tạo ma trận tương quan và dùng go.Heatmap hoặc px.imshow.\n"
        "- Giữ số trace vừa phải (≤5). Đặt tiêu đề, nhãn trục rõ ràng. Dùng format ngày chuẩn nếu trục x là thời gian."
    )
    
    prompt = (
        f"{system_prompt}\n\n"
        f"Câu hỏi: {question}\n"
        f"Chart type hint: {chart_type_hint or 'auto'}\n"
        f"Chart request JSON: {chart_request_json}\n"
        f"Các cột sẵn có: {columns}\n"
        f"Dữ liệu mẫu (JSON):\n{data_json}\n\n"
        f"{guidance}"
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


def render_chart_from_code(code: Optional[str], df: pd.DataFrame) -> Optional[go.Figure]:
    if not code:
        return None
    code = code.strip()
    if code.lower().startswith("python"):
        newline_idx = code.find("\n")
        code = code[newline_idx + 1:] if newline_idx != -1 else ""
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
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        name='Close Price',
        line=dict(color='#2E86AB', width=2),
        hovertemplate='Date: %{x}<br>Close: $%{y:.2f}<extra></extra>'
    ))
    
    # Thêm moving average 20 ngày nếu có đủ dữ liệu
    if len(df) >= 20:
        df['ma20'] = df['close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ma20'],
            mode='lines',
            name='MA 20',
            line=dict(color='#F77F00', width=1, dash='dash'),
            hovertemplate='Date: %{x}<br>MA20: $%{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title or f'{ticker} - Biểu đồ giá',
        xaxis_title='Ngày',
        yaxis_title='Giá ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_candlestick_chart(df: pd.DataFrame, ticker: str, title: str = None) -> go.Figure:
    """Tạo biểu đồ nến cho giá cổ phiếu."""
    if df.empty or not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        return None
    
    # Create figure with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title or f'{ticker} - Biểu đồ nến', 'Khối lượng giao dịch')
    )
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
        increasing_line_color='#26A69A',
        decreasing_line_color='#EF5350'
    ), row=1, col=1)
    
    # Volume bar chart
    colors = ['#26A69A' if close >= open else '#EF5350' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)
    
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Ngày", row=2, col=1)
    fig.update_yaxes(title_text="Giá ($)", row=1, col=1)
    fig.update_yaxes(title_text="Khối lượng", row=2, col=1)
    
    return fig


def create_comparison_chart(df: pd.DataFrame, tickers: list, title: str = None) -> go.Figure:
    """Tạo biểu đồ so sánh nhiều cổ phiếu."""
    if df.empty or 'ticker' not in df.columns:
        return None
    
    fig = go.Figure()
    
    colors = ['#2E86AB', '#F77F00', '#06A77D', '#D62828', '#F4A259', '#4059AD']
    
    for i, ticker in enumerate(tickers):
        ticker_df = df[df['ticker'] == ticker].copy()
        if not ticker_df.empty:
            # Normalize to percentage change from first value
            first_close = ticker_df['close'].iloc[0]
            ticker_df['pct_change'] = ((ticker_df['close'] - first_close) / first_close) * 100
            
            fig.add_trace(go.Scatter(
                x=ticker_df['date'],
                y=ticker_df['pct_change'],
                mode='lines',
                name=ticker,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Change: %{{y:.2f}}%<extra></extra>'
            ))
    
    fig.update_layout(
        title=title or 'So sánh biến động giá (%)',
        xaxis_title='Ngày',
        yaxis_title='Thay đổi (%)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_volume_chart(df: pd.DataFrame, ticker: str, title: str = None) -> go.Figure:
    """Tạo biểu đồ khối lượng giao dịch."""
    if df.empty or 'volume' not in df.columns:
        return None
    
    fig = go.Figure()
    
    colors = ['#26A69A' if close >= open else '#EF5350' 
              for close, open in zip(df['close'], df['open'])]
    
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        hovertemplate='Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
    ))
    
    # Add moving average of volume
    if len(df) >= 20:
        df['vol_ma20'] = df['volume'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['vol_ma20'],
            mode='lines',
            name='Volume MA 20',
            line=dict(color='#F77F00', width=2),
            hovertemplate='Date: %{x}<br>Vol MA20: %{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title or f'{ticker} - Khối lượng giao dịch',
        xaxis_title='Ngày',
        yaxis_title='Khối lượng',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        showlegend=True
    )
    
    return fig


def fetch_chart_data(question: str, ticker: str, chart_type: str) -> pd.DataFrame:
    """Lấy dữ liệu từ database để vẽ biểu đồ."""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Xác định khoảng thời gian
        start_date, end_date = extract_date_range(question)
        date_parts = extract_date_parts(question)
        
        # Xây dựng SQL query
        if chart_type == "comparison":
            # So sánh nhiều công ty - cần tìm tất cả tickers trong câu hỏi
            # Fallback: lấy tất cả công ty trong 1 tháng gần nhất
            sql = """
                SELECT date, ticker, open, high, low, close, volume
                FROM prices
                WHERE date >= date('now', '-1 month')
                ORDER BY date ASC, ticker ASC
            """
        else:
            # Single ticker
            where_clauses = [f"ticker = '{ticker}'"]
            
            if start_date and end_date:
                where_clauses.append(f"date(date) BETWEEN date('{start_date}') AND date('{end_date}')")
            elif 'year' in date_parts:
                where_clauses.append(f"strftime('%Y', date) = '{date_parts['year']}'")
            elif 'month' in date_parts and 'year' in date_parts:
                where_clauses.append(f"strftime('%Y-%m', date) = '{date_parts['year']}-{date_parts['month']}'")
            else:
                # Default: last 3 months
                where_clauses.append("date >= date('now', '-3 months')")
            
            where_clause = " AND ".join(where_clauses)
            
            sql = f"""
                SELECT date, open, high, low, close, volume
                FROM prices
                WHERE {where_clause}
                ORDER BY date ASC
            """
        
        df = pd.read_sql_query(sql, conn)
        
        # Convert date to datetime
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    except Exception as e:
        print(f"Error fetching chart data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


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
    
    # Nếu không có ticker, thử trích xuất
    if not ticker:
        ticker = extract_ticker(question)
    
    # Nếu vẫn không có ticker, không vẽ được
    if not ticker and chart_type != "comparison":
        return {**state, "chart": None, "chart_error": "Không xác định được mã cổ phiếu"}
    
    # Nếu đã có df từ SQL execution, dùng luôn, nếu không thì fetch riêng
    if df is None or df.empty or 'date' not in df.columns:
        df = fetch_chart_data(question, ticker, chart_type)
    
    if df.empty:
        return {**state, "chart": None, "chart_error": "Không có dữ liệu để vẽ biểu đồ"}
    
    # Ensure date column is datetime
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
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
            "chart_error": error_msg or "Không thể tạo biểu đồ từ mô tả của bạn. Hãy cụ thể hơn hoặc thử lại."
        }
    
    return {**state, "chart": chart, "chart_error": None}
