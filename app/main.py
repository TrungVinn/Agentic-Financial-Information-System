import sys
from pathlib import Path

# Thêm project root vào PYTHONPATH để import được module agents/*
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import streamlit as st
import pandas as pd

from graphs.djia_graph import run_djia_graph


st.set_page_config(page_title="DJIA Q&A Chat", layout="wide")

with st.sidebar:
    st.header("DJIA Chat Agent")
    st.markdown("Hỏi bằng tiếng Việt hoặc tiếng Anh về DJIA.")
    if st.button("Xóa hội thoại"):
        st.session_state.pop("messages", None)
        st.rerun()

# Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = []  # mỗi item: {role, content, sql, used_sample, df_json}

st.title("Chat với DJIA Agent")

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg.get("role", "assistant")):
        st.write(msg.get("content", ""))
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
        note = msg.get("note")
        if note:
            st.caption(note)

# Ô nhập chat
user_input = st.chat_input("Nhập câu hỏi...")
if user_input:
    # Lưu tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Trả lời từ agent
    with st.chat_message("assistant"):
        with st.spinner("Đang truy vấn..."):
            try:
                result = run_djia_graph(user_input)
                # Hiển thị answer ngắn gọn
                st.write(result.get("answer", ""))
                # SQL và bảng
                if result.get("sql"):
                    with st.expander("SQL đã chạy"):
                        st.code(result.get("sql"), language="sql")
                df = result.get("df")
                if isinstance(df, pd.DataFrame) and not df.empty:
                    with st.expander("Bảng kết quả"):
                        st.dataframe(df)
                note = "Đã sử dụng SQL mẫu." if result.get("used_sample") else "SQL được sinh bởi Gemini hoặc tinh chỉnh tự động."
                st.caption(note)

                # Lưu tin nhắn trợ lý vào lịch sử
                df_json = ""
                try:
                    df_json = df.to_json(orient="records") if isinstance(df, pd.DataFrame) else ""
                except Exception:
                    df_json = ""
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.get("answer", ""),
                    "sql": result.get("sql", ""),
                    "used_sample": result.get("used_sample", False),
                    "df_json": df_json,
                    "note": note,
                })
            except Exception as e:
                err_msg = f"Lỗi: {e}"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})


