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

### Yêu Cầu Hệ Thống
- **Python 3.11+**: [Tải Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Tải Node.js](https://nodejs.org/)
- **PostgreSQL 14+**: [Tải PostgreSQL](https://www.postgresql.org/download/)
- **npm hoặc yarn**: Đi kèm với Node.js

### Bước 1: Tải Code
```bash
# Clone repository
git clone https://github.com/TrungVinn/Agentic-Financial-Information-System.git
cd Agentic-Financial-Information-System
# Hoặc tải file ZIP và giải nén
```

### Bước 2: Cài Đặt Backend (Django)

1. **Tạo và kích hoạt virtual environment:**
```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\Activate
# Linux/Mac:
source .venv/bin/activate
```

2. **Cài đặt thư viện Python:**
```bash
pip install -r requirements.txt
```

3. **Cấu hình API Key và Database:**

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

   **Lấy API Key miễn phí:**
   - Truy cập: https://aistudio.google.com/app/apikey
   - Đăng nhập bằng tài khoản Google
   - Nhấn "Create API Key" và copy key vào file `.env`

4. **Khởi tạo Database:**

   a. **Cài đặt PostgreSQL** (nếu chưa có):
   - Tải và cài đặt từ: https://www.postgresql.org/download/

   b. **Tạo Database:**
   ```sql
   -- Kết nối PostgreSQL
   psql -U postgres
   -- Tạo database
   CREATE DATABASE djia;
   \q
   ```

   c. **Import dữ liệu:**
   ```bash
   # Đảm bảo đã kích hoạt virtual environment
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

5. **Chạy migrations Django:**
```bash
# Di chuyển vào thư mục backend
cd backend

# Chạy migrations để tạo bảng cho chat history
python manage.py migrate

# Tạo superuser (tùy chọn, để truy cập Django admin)
python manage.py createsuperuser
```

### Bước 3: Cài Đặt Frontend (Vite + React)

1. **Cài đặt dependencies:**
```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt npm packages
npm install
```

### Bước 4: Chạy Ứng Dụng

**Cần chạy cả Backend và Frontend:**

1. **Terminal 1 - Chạy Django Backend:**
```bash
# Đảm bảo đã kích hoạt virtual environment
cd backend
python manage.py runserver
```

Backend sẽ chạy tại: **http://localhost:8000**

2. **Terminal 2 - Chạy Vite Frontend:**
```bash
cd frontend
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:5173**

3. **Mở trình duyệt:**
   - Truy cập: **http://localhost:5173**
   - Frontend sẽ tự động kết nối với backend qua proxy

---

## Hướng Dẫn Sử Dụng

### Bắt Đầu Nhanh

1. **Đảm bảo cả Backend và Frontend đang chạy:**
   - Backend: http://localhost:8000
   - Frontend: http://localhost:5173

2. **Mở trình duyệt** tại http://localhost:5173

3. **Sử dụng ứng dụng:**
   - **Chưa đăng nhập**: Có thể chat ngay, lịch sử lưu cục bộ (localStorage)
   - **Đăng nhập/Đăng ký**: Click nút "Đăng nhập / Đăng ký" ở góc phải trên
     - Đăng ký tài khoản mới hoặc đăng nhập
     - Lịch sử chat sẽ được lưu trên server và đồng bộ giữa các thiết bị

4. **Nhập câu hỏi** vào ô chat ở cuối trang

5. **Nhận câu trả lời** ngay lập tức với:
   - Câu trả lời ngắn gọn
   - SQL đã chạy (có thể đóng/mở)
   - Bảng dữ liệu chi tiết (có thể đóng/mở)
   - Biểu đồ (nếu yêu cầu)

### Tính Năng Chính

#### Chat Interface
- **Giao diện**: Dark theme, sidebar lịch sử, chat căn giữa
- **Lịch sử hội thoại**: 
  - Sidebar bên trái hiển thị tất cả các phiên chat
  - Click vào phiên chat để xem lại lịch sử
  - Có thể xóa phiên chat
- **Đóng/Mở sections**: Click vào "SQL đã chạy" hoặc "Bảng dữ liệu" để đóng/mở

#### Hệ Thống Tài Khoản
- **Đăng ký/Đăng nhập**: Lưu lịch sử chat trên server
- **Đồng bộ**: Lịch sử được đồng bộ giữa các thiết bị khi đăng nhập
- **Local storage**: Nếu chưa đăng nhập, lịch sử lưu cục bộ trên trình duyệt

#### Django Admin (Tùy chọn)
- Truy cập: http://localhost:8000/admin
- Đăng nhập bằng superuser đã tạo
- Xem và quản lý:
  - Conversations (phiên chat)
  - Messages (tin nhắn)
  - Users (người dùng)

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

## Cấu Trúc Project

```
Agentic-Financial-Information-System/
├── backend/                 # Django Backend
│   ├── api/                # Django REST API app
│   │   ├── models.py       # Conversation, Message models
│   │   ├── views.py        # API endpoints
│   │   └── urls.py         # URL routing
│   ├── core/               # Django project settings
│   │   ├── settings.py      # Django configuration
│   │   └── urls.py         # Main URL routing
│   ├── graphs/             # LangGraph multi-agent system
│   ├── nodes/              # Agent nodes
│   ├── db/                 # Database initialization
│   ├── manage.py           # Django management script
│   └── config.py           # Database configuration
│
├── frontend/               # Vite + React Frontend
│   ├── src/
│   │   ├── App.tsx         # Main React component
│   │   ├── App.css         # Styles
│   │   └── main.tsx        # Entry point
│   ├── vite.config.ts      # Vite configuration
│   └── package.json        # npm dependencies
│
├── .env                    # Environment variables (tạo file này)
├── requirements.txt        # Python dependencies
└── README.md              # File này
```