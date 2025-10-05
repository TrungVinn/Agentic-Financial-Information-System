# DJIA Multi-Agent (LangChain + Gemini + SQLite + Streamlit)

Ứng dụng cho phép đặt câu hỏi (Việt/Anh) về dữ liệu DJIA (companies/prices), hiển thị câu lệnh SQL, bảng kết quả và câu trả lời ngắn. Giao diện chat như ChatGPT.

##  Cài đặt
```bash
python -m venv .venv
# Windows PowerShell
.venv/Scripts/Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

## Thiết lập API Key
Tạo file `.env` ở thư mục gốc:
```
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=your_gemini_key_here
```
(Ứng dụng chấp nhận một trong hai; có thể đặt cùng giá trị.)

## Chuẩn bị dữ liệu & Database
Dữ liệu CSV có sẵn:
- data/djia_companies_20250426.csv
- data/djia_prices_20250426.csv

Sinh SQLite DB:
```bash
python db/init_db.py
```

## Chạy ứng dụng
```bash
streamlit run app/main.py
```

## Cách dùng
- Nhập câu hỏi vào ô chat (Việt/Anh), ví dụ:
  - "What was the closing price of Microsoft on March 15, 2024?"
  - "On what date did Walmart execute a stock split, and what was the split ratio?"
  - "Which company had a higher closing price on 2025-01-15, Apple or Microsoft?"
  - "What was the average closing price of Apple during Q1 2025?"
- Mỗi câu trả lời gồm:
  - SQL đã chạy
  - Bảng kết quả
  - Answer ngắn gọn
- Agent ưu tiên tái sử dụng SQL mẫu từ `data/sql_samples.sql`. Nếu không có, sẽ sinh SQL bằng Gemini

## Cấu trúc chính
- agents/djia_agent.py: Agent xử lý hỏi đáp, khớp mẫu, sinh SQL, chạy SQLite, trích xuất answer.
- data/sql_samples.sql: Kho câu lệnh SQL mẫu theo nhóm câu hỏi (factual/comparative/analytical…).
- db/init_db.py: Tạo DB từ CSV, tạo index.
- app/main.py: Giao diện chat Streamlit (hiển thị SQL/bảng/answer, lưu lịch sử hội thoại).
- config.py: Định nghĩa đường dẫn, schema bảng.
