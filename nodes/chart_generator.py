from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from config import DB_PATH
from nodes.utils import extract_ticker, extract_date_range, extract_date_parts


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
    
    # Tạo biểu đồ theo loại
    chart = None
    try:
        if chart_type == "candlestick":
            chart = create_candlestick_chart(df, ticker)
        elif chart_type == "volume":
            chart = create_volume_chart(df, ticker)
        elif chart_type == "comparison":
            # Lấy danh sách tickers từ df
            tickers = df['ticker'].unique().tolist() if 'ticker' in df.columns else []
            if tickers:
                chart = create_comparison_chart(df, tickers)
        else:  # default: line chart
            chart = create_line_chart(df, ticker)
    except Exception as e:
        print(f"Error creating chart: {e}")
        return {**state, "chart": None, "chart_error": str(e)}
    
    return {**state, "chart": chart, "chart_error": None}
