# DJIA Multi-Agent System (LangGraph + Gemini + SQLite + Streamlit)

Hệ thống multi-agent cho phép đặt câu hỏi (Việt/Anh) về dữ liệu DJIA, sử dụng LangGraph để điều phối các agent chuyên biệt. Mỗi agent có nhiệm vụ riêng: trích xuất ticker, tìm SQL mẫu, sinh SQL, thực thi và tóm tắt kết quả.

## ⭐ Tính năng mới (2025)

### 🎨 Tự động vẽ biểu đồ giá
- **Line Chart**: Xu hướng giá với Moving Average
- **Candlestick Chart**: Biểu đồ nến OHLC + Volume
- **Comparison Chart**: So sánh nhiều cổ phiếu
- **Volume Chart**: Phân tích khối lượng giao dịch

### 📊 Phân tích thống kê nâng cao
- Standard Deviation (Độ lệch chuẩn)
- Volatility (Biến động giá)
- Correlation (Tương quan)
- CAGR (Tỷ lệ tăng trưởng kép)
- Median, Moving Averages

### 🧠 Xử lý câu hỏi phức tạp
- Multi-step queries
- Company rankings (Top 3, Bottom 3)
- Statistical analysis
- Time-series analysis

**📚 Xem thêm:**
- [ENHANCEMENTS.md](ENHANCEMENTS.md) - Tài liệu kỹ thuật chi tiết
- [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md) - Hướng dẫn người dùng đầy đủ

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

### **Tab Chat**: Nhập câu hỏi vào ô chat (Việt/Anh)

#### Câu hỏi cơ bản:
- "What was the closing price of Microsoft on March 15, 2024?"
- "Which company had a higher closing price on 2025-01-15, Apple or Microsoft?"
- "What was the average closing price of Boeing from July through December 2023?"

#### ⭐ Vẽ biểu đồ (MỚI):
- "Vẽ biểu đồ giá Apple trong tháng 3/2024"
- "Draw a candlestick chart for Microsoft in Q1 2024"
- "So sánh xu hướng giá Apple và Microsoft trong 2024"
- "Show me the price trend of Boeing in 2024"

#### 📊 Phân tích thống kê (MỚI):
- "Độ lệch chuẩn của giá Apple trong 2024?"
- "What was the volatility of Microsoft in 2024?"
- "Correlation between Apple and Microsoft in 2024?"
- "Top 3 companies by total return in 2024"

### **Tab SQL Runner**: Chạy SQL trực tiếp trên database

### Mỗi câu trả lời gồm:
- ✅ Câu trả lời ngắn gọn (văn bản)
- ✅ **Biểu đồ tương tác (MỚI)** - nếu câu hỏi yêu cầu
- ✅ SQL đã thực thi (trong expander)
- ✅ Bảng kết quả (trong expander)
- ✅ Ghi chú về nguồn SQL

## Kiến trúc Multi-Agent

### **Luồng hoạt động (Cập nhật 2025):**
```
Câu hỏi → Query Planner (MỚI) → SQL Template Matcher → SQL Executor 
                                        ↓ (nếu không tìm thấy)
                                  SQL LLM Generator
                                        ↓
                            Chart Generator (MỚI) → Answer Summarizer
```

### **Các Agent chuyên biệt:**

0. **⭐ Query Planner** (`nodes/planner.py`) - **MỚI**
   - Phân tích độ phức tạp của câu hỏi
   - Phát hiện yêu cầu vẽ biểu đồ
   - Xác định loại biểu đồ phù hợp
   - Tạo execution plan cho câu hỏi phức tạp

1. **SQL Template Matcher** (`nodes/sql_template_matcher.py`)
   - Trích xuất ticker từ câu hỏi
   - Tìm SQL mẫu phù hợp từ `data/sql_samples.sql` (80+ templates)
   - Sử dụng heuristic rules + LLM validation
   - Hỗ trợ: factual, comparative, analytical, statistical

2. **SQL LLM Generator** (`nodes/sql_llm_generator.py`)
   - Sinh SQL mới bằng Gemini AI khi không có mẫu phù hợp
   - Phân tích câu hỏi và tạo SQL tương ứng

3. **SQL Executor** (`nodes/sql_executor.py`)
   - Thực thi SQL trên SQLite database
   - Thay thế parameters và trả về kết quả
   - Xử lý lỗi và validation

4. **⭐ Chart Generator** (`nodes/chart_generator.py`) - **MỚI**
   - Tạo 4 loại biểu đồ: Line, Candlestick, Comparison, Volume
   - Sử dụng Plotly cho biểu đồ tương tác
   - Tự động thêm Moving Averages
   - Responsive và có thể zoom/pan

5. **Answer Summarizer** (`nodes/answer_summarizer.py`)
   - Tóm tắt kết quả SQL thành câu trả lời tự nhiên
   - Sử dụng Gemini AI để tạo câu trả lời ngắn gọn

### **Công cụ hỗ trợ:**
- **Utils** (`nodes/utils.py`): Chuẩn hóa text, trích xuất ngày tháng, ticker
- **Graph** (`graphs/djia_graph.py`): Điều phối workflow với LangGraph (cập nhật)
- **Frontend** (`app/main.py`): Giao diện Streamlit với chat history + charts

## 📁 Cấu trúc dự án
```
workspace/
├── nodes/                       # Các agent chuyên biệt
│   ├── planner.py               # ⭐ Query planner (MỚI)
│   ├── chart_generator.py       # ⭐ Chart generation (MỚI)
│   ├── sql_template_matcher.py  # Tìm SQL mẫu + trích xuất ticker
│   ├── sql_llm_generator.py     # Sinh SQL bằng AI
│   ├── sql_executor.py          # Thực thi SQL
│   ├── answer_summarizer.py     # Tóm tắt kết quả
│   └── utils.py                 # Công cụ hỗ trợ
├── graphs/
│   └── djia_graph.py            # LangGraph workflow (cập nhật)
├── app/
│   └── main.py                  # Frontend Streamlit (cập nhật)
├── data/
│   ├── sql_samples.sql          # 80+ SQL templates (mở rộng)
│   ├── djia_companies_*.csv     # Dữ liệu công ty
│   └── djia_prices_*.csv        # Dữ liệu giá
├── db/
│   └── init_db.py               # Khởi tạo database
├── config.py                    # Cấu hình đường dẫn
├── ENHANCEMENTS.md              # ⭐ Tài liệu kỹ thuật (MỚI)
├── HUONG_DAN_SU_DUNG.md         # ⭐ Hướng dẫn đầy đủ (MỚI)
├── SUMMARY.md                   # ⭐ Tổng kết cải tiến (MỚI)
└── test_enhancements.py         # ⭐ Test suite (MỚI)
```

## 📚 Tài liệu

- **README.md** (file này) - Tổng quan hệ thống
- **[ENHANCEMENTS.md](ENHANCEMENTS.md)** - Tài liệu kỹ thuật chi tiết về tính năng mới
- **[HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)** - Hướng dẫn sử dụng đầy đủ (Tiếng Việt)
- **[SUMMARY.md](SUMMARY.md)** - Tổng kết các cải tiến 2025

## 🧪 Testing

Chạy test suite:
```bash
python test_enhancements.py
```

Test bao gồm:
- Simple queries
- Chart generation (4 types)
- Statistical analysis
- Multi-company rankings
