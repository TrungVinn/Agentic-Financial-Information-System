import sys
from pathlib import Path

# Thêm project root vào PYTHONPATH để import được module agents/*
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import streamlit as st
import pandas as pd
import sqlite3
import plotly.io as pio

from graphs.djia_graph import run_djia_graph


st.set_page_config(page_title="DJIA Q&A Chat", layout="wide")

with st.sidebar:
    st.header("DJIA Chat Agent")
    if st.button("Xóa hội thoại"):
        st.session_state.pop("messages", None)
        st.rerun()

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []  # mỗi item: {role, content, sql, used_sample, df_json}

st.title("Chat với DJIA Agent")

tab_chat, tab_sql = st.tabs(["Chat", "SQL Runner"])

with tab_chat:
    # Container cho chat history
    chat_container = st.container()
    
    with chat_container:
        # Hiển thị lịch sử
        for msg in st.session_state.messages:
            with st.chat_message(msg.get("role", "assistant")):
                st.write(msg.get("content", ""))
                
                # Hiển thị biểu đồ (nếu có trong lịch sử)
                chart_json = msg.get("chart_json")
                if chart_json:
                    try:
                        import plotly.graph_objects as go
                        import json
                        chart_dict = json.loads(chart_json)
                        chart = go.Figure(chart_dict)
                        st.plotly_chart(chart, use_container_width=True)
                    except Exception:
                        pass
                
                sql = msg.get("sql")
                if sql:
                    with st.expander("SQL đã chạy"):
                        st.code(sql, language="sql")
                df_json = msg.get("df_json")
                if df_json:
                    try:
                        df = pd.read_json(df_json)
                        with st.expander("Bảng kết quả"):
                            st.dataframe(df)
                    except Exception:
                        pass
                chart_json = msg.get("chart_json")
                if chart_json:
                    try:
                        fig = pio.from_json(chart_json)
                        with st.expander("Biểu đồ giá"):
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass
                note = msg.get("note")
                if note:
                    st.caption(note)

    # Ô nhập chat - luôn ở cuối trang
    st.markdown("---")  # Thêm đường phân cách
    user_input = st.chat_input("Nhập câu hỏi...")
    if user_input:
        # Lưu tin nhắn người dùng
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Hiển thị tin nhắn người dùng trong container
        with chat_container:
            with st.chat_message("user"):
                st.write(user_input)

        # Trả lời từ agent
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Đang truy vấn..."):
                    try:
                        result = run_djia_graph(user_input)
                        
                        
                        # Hiển thị answer ngắn gọn
                        st.write(result.get("answer", ""))
                        
                        # Hiển thị biểu đồ (nếu có)
                        chart = result.get("chart")
                        if chart is not None:
                            st.plotly_chart(chart, use_container_width=True)
                        
                        # SQL và bảng
                        if result.get("sql"):
                            with st.expander("SQL đã chạy"):
                                st.code(result.get("sql"), language="sql")
                        df = result.get("df")
                        if isinstance(df, pd.DataFrame) and not df.empty:
                            with st.expander("Bảng kết quả"):
                                st.dataframe(df)
                        chart_json = result.get("chart_json")
                        if chart_json:
                            try:
                                fig = pio.from_json(chart_json)
                                with st.expander("Biểu đồ giá"):
                                    st.plotly_chart(fig, use_container_width=True)
                            except Exception as chart_err:
                                st.warning(f"Không thể hiển thị biểu đồ: {chart_err}")
                        
                        note = "Đã sử dụng SQL mẫu." if result.get("used_sample") else "SQL được sinh bởi Gemini hoặc tinh chỉnh tự động."
                        st.caption(note)

                        # Lưu tin nhắn trợ lý vào lịch sử
                        df_json = ""
                        try:
                            df_json = df.to_json(orient="records") if isinstance(df, pd.DataFrame) else ""
                        except Exception:
                            df_json = ""
                        
                        # Convert chart to JSON for storage
                        chart_json = ""
                        try:
                            if chart is not None:
                                chart_json = chart.to_json()
                        except Exception:
                            chart_json = ""
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result.get("answer", ""),
                            "sql": result.get("sql", ""),
                            "used_sample": result.get("used_sample", False),
                            "df_json": df_json,
                            "chart_json": chart_json,
                            "note": note,
                            "chart_json": chart_json,
                        })
                    except Exception as e:
                        err_msg = f"Lỗi: {e}"
                        st.error(err_msg)
                        st.session_state.messages.append({"role": "assistant", "content": err_msg})

with tab_sql:
    st.subheader("Chạy SQL trực tiếp")
    user_sql = st.text_area("SQL", height=180)
    if st.button("Chạy SQL", type="primary"):
        # Loại dòng comment để hiển thị gọn gàng
        display_sql = "\n".join([line for line in user_sql.splitlines() if not line.strip().startswith("--")]).strip()
        try:
            # Dùng DB_PATH
            from config import DB_PATH
            conn = sqlite3.connect(str(DB_PATH))
            df = pd.read_sql_query(user_sql, conn)
            conn.close()
            st.success("Chạy thành công")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Lỗi khi chạy SQL: {e}")


