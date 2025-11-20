# DJIA Multi-Agent System (LangGraph + Gemini + SQLite + Streamlit)

Hệ thống multi-agent cho phép đặt câu hỏi (Việt/Anh) về dữ liệu DJIA, sử dụng LangGraph để điều phối các agent chuyên biệt. Mỗi agent có nhiệm vụ riêng: trích xuất ticker, tìm SQL mẫu, sinh SQL, thực thi và tóm tắt kết quả.

## Cài đặt
```bash
python -m venv .venv
# Windows PowerShell
.venv/Scripts/Activate
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
- `data/djia_companies_20250426.csv` - Thông tin công ty
- `data/djia_prices_20250426.csv` - Dữ liệu giá cổ phiếu

Sinh SQLite DB:
```bash
python db/init_db.py
```

## Chạy ứng dụng
```bash
streamlit run app/main.py
```

## 💬 Cách dùng
- **Tab Chat**: Nhập câu hỏi vào ô chat (Việt/Anh), ví dụ:
  - "What was the closing price of Microsoft on March 15, 2024?"
  - "Which company had a higher closing price on 2025-01-15, Apple or Microsoft?"
  - "What was the average closing price of Boeing from July through December 2023?"
  - "Which company had the highest closing price on July 1, 2024?"
- **Tab SQL Runner**: Chạy SQL trực tiếp trên database

Mỗi câu trả lời gồm:
- SQL đã thực thi (với parameters đã thay thế)
- Bảng kết quả
- Câu trả lời ngắn gọn
- Ghi chú về nguồn SQL (mẫu hoặc AI sinh)

## Kiến trúc Multi-Agent

### **Luồng hoạt động:**
```
Câu hỏi → SQL Template Matcher → SQL Executor → Answer Summarizer
                    ↓ (nếu không tìm thấy)
              SQL LLM Generator
```

### **Các Agent chuyên biệt:**

1. **SQL Template Matcher** (`nodes/sql_template_matcher.py`)
   - Trích xuất ticker từ câu hỏi
   - Tìm SQL mẫu phù hợp từ `data/sql_samples.sql`
   - Sử dụng heuristic rules + LLM validation
   - Hỗ trợ câu hỏi: factual, comparative, analytical

2. **SQL LLM Generator** (`nodes/sql_llm_generator.py`)
   - Sinh SQL mới bằng Gemini AI khi không có mẫu phù hợp
   - Phân tích câu hỏi và tạo SQL tương ứng

3. **SQL Executor** (`nodes/sql_executor.py`)
   - Thực thi SQL trên SQLite database
   - Thay thế parameters và trả về kết quả
   - Xử lý lỗi và validation

4. **Answer Summarizer** (`nodes/answer_summarizer.py`)
   - Tóm tắt kết quả SQL thành câu trả lời tự nhiên
   - Sử dụng Gemini AI để tạo câu trả lời ngắn gọn

### **Công cụ hỗ trợ:**
- **Utils** (`nodes/utils.py`): Chuẩn hóa text, trích xuất ngày tháng, ticker
- **Graph** (`graphs/djia_graph.py`): Điều phối workflow với LangGraph
- **Frontend** (`app/main.py`): Giao diện Streamlit với chat history

## 📁 Cấu trúc dự án
```
langchain1/
├── nodes/                    # Các agent chuyên biệt
│   ├── sql_template_matcher.py  # Tìm SQL mẫu + trích xuất ticker
│   ├── sql_llm_generator.py     # Sinh SQL bằng AI
│   ├── sql_executor.py          # Thực thi SQL
│   ├── answer_summarizer.py     # Tóm tắt kết quả
│   └── utils.py                 # Công cụ hỗ trợ
├── graphs/
│   └── djia_graph.py            # LangGraph workflow
├── app/
│   └── main.py                  # Frontend Streamlit
├── data/
│   ├── sql_samples.sql          # Kho SQL mẫu
│   ├── djia_companies_*.csv     # Dữ liệu công ty
│   └── djia_prices_*.csv        # Dữ liệu giá
├── db/
│   └── init_db.py               # Khởi tạo database
└── config.py                    # Cấu hình đường dẫn
```
