# DJIA Q&A Chat - Hệ Thống Hỏi Đáp Thông Minh Về Chứng Khoán

> **Hỏi đáp về dữ liệu chứng khoán DJIA bằng ngôn ngữ tự nhiên (Tiếng Việt & Tiếng Anh)**

Ứng dụng AI chatbot thông minh giúp bạn tra cứu và phân tích dữ liệu của 30 công ty trong chỉ số Dow Jones Industrial Average (DJIA) chỉ bằng cách đặt câu hỏi tự nhiên. 
---

## Tính Năng Nổi Bật

### Hỏi Đáp Thông Minh
- **Tiếng Việt & Tiếng Anh**: "Giá đóng cửa của Apple vào ngày XX?" hoặc "What was Microsoft's closing price?"
- **Tự động hiểu ý**: Nhận biết tên công ty, ngày tháng, loại dữ liệu cần tra
- **Mẫu SQL tích hợp**: Trả lời nhanh các câu hỏi phổ biến
- **AI sinh SQL tự động**: Xử lý câu hỏi phức tạp bằng Gemini AI

### Vẽ Biểu Đồ Tự Động
Chỉ cần nói "vẽ biểu đồ" hoặc "plot" là có ngay biểu đồ tương tác:

### Phân Tích Đa Dạng
- **So sánh**: "Apple hay Microsoft có giá cao hơn?"
- **Thống kê**: "Giá trung bình của Boeing trong quý 1/2024?"
- **Xu hướng**: "Biến động giá của Tesla trong năm 2024?"
- **Ranking**: "Top 3 công ty tăng trưởng mạnh nhất?"

### Giao Diện Thân Thiện
- **Chat interface** đơn giản, dễ sử dụng
- **Lịch sử hội thoại** lưu tất cả câu hỏi và trả lời
- **Hiển thị SQL** (tùy chọn) để bạn học hỏi
- **Export biểu đồ**

---

### API Key (Miễn Phí)
- **Google Gemini API**: Đăng ký miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## Hướng Dẫn Cài Đặt 

### Bước 1: Tải Code
```bash
# Clone repository
git clone https://github.com/TrungVinn/Agentic-Financial-Information-System.git
# Hoặc tải file ZIP và giải nén
```

### Bước 2: Cài Đặt Python Environment
```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
.venv\Scripts\Activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### Bước 3: Cấu Hình API Key

1. **Lấy API Key miễn phí:**
   - Truy cập: https://aistudio.google.com/app/apikey
   - Đăng nhập bằng tài khoản Google
   - Nhấn "Create API Key" và copy key

2. **Tạo file `.env`:**
   
   Tạo file `.env` trong thư mục gốc của project:

   ```env
   # Google Gemini API Key
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_API_KEY=your_gemini_api_key_here

   # PostgreSQL Database Configuration
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=djia
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password_here
   ```

### Bước 4: Khởi Tạo Database
1. Cài đặt PostgreSQL
- Tải và cài đặt từ: https://www.postgresql.org/download/windows/

2. Tạo Database
```sql
-- Kết nối PostgreSQL
psql -U postgres
-- Tạo database
CREATE DATABASE djia;
\q
```

```bash
python db/init_db.py
```

Script này sẽ:
- Tạo bảng `companies` và `prices`
- Import dữ liệu từ CSV files
- Tạo indexes để tăng tốc độ truy vấn


**Kết quả mong đợi:**
```
Đang import dữ liệu companies...
Đã import 30 records vào bảng companies
Đang import dữ liệu prices...
Đã import 15060 records vào bảng prices
Database đã được tạo thành công!
Các bảng trong database: ['companies', 'prices']
Số lượng companies: 30
Số lượng prices: 15060
```

### Bước 5: Chạy Ứng Dụng
```bash
# Khởi động Streamlit
streamlit run app/main.py
```

**Ứng dụng sẽ tự động mở tại:** http://localhost:8501

---

## Hướng Dẫn Sử Dụng

### Bắt Đầu Nhanh

1. **Mở trình duyệt** tại http://localhost:8501
2. **Nhập câu hỏi** vào ô chat ở cuối trang
3. **Nhận câu trả lời** ngay lập tức với:
   - Câu trả lời ngắn gọn
   - Biểu đồ (nếu yêu cầu)
   - SQL đã chạy (trong expander)
   - Bảng dữ liệu chi tiết

### Các Tab Trong Ứng Dụng

#### Tab 1: Chat (Hỏi Đáp)
- Nhập câu hỏi tự nhiên
- Xem câu trả lời ngay lập tức
- Lịch sử hội thoại được lưu

#### Tab 2: SQL Runner (Nâng Cao)
- Chạy SQL trực tiếp nếu bạn biết SQL
- Xem cấu trúc database
- Thử nghiệm các query phức tạp

---

## Dữ Liệu Có Sẵn

### 30 Công Ty DJIA
Apple (AAPL), Microsoft (MSFT), Boeing (BA), Coca-Cola (KO), Disney (DIS), Goldman Sachs (GS), IBM (IBM), Intel (INTC), JPMorgan (JPM), Johnson & Johnson (JNJ), McDonald's (MCD), Nike (NKE), Visa (V), Walmart (WMT), và 16 công ty khác.

### Thông Tin Công Ty
- Tên và mã cổ phiếu (ticker)
- Ngành nghề (sector)
- Lĩnh vực (industry)
- Vốn hóa thị trường
- P/E ratio, dividend yield
- Giá 52 tuần cao/thấp

### Dữ Liệu Giá
- Giá mở cửa (open)
- Giá cao nhất (high)
- Giá thấp nhất (low)
- Giá đóng cửa (close)
- Khối lượng giao dịch (volume)
- Cổ tức (dividends)
- Tỷ lệ chia tách cổ phiếu (stock splits)

**Khoảng thời gian:** Dữ liệu lịch sử từ 2020 đến 2025

---
