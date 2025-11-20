# DJIA Q&A Chat - Hệ Thống Hỏi Đáp Thông Minh Về Chứng Khoán

> **Hỏi đáp về dữ liệu chứng khoán DJIA bằng ngôn ngữ tự nhiên (Tiếng Việt & Tiếng Anh)**

Ứng dụng AI chatbot thông minh giúp bạn tra cứu và phân tích dữ liệu của 30 công ty trong chỉ số Dow Jones Industrial Average (DJIA) chỉ bằng cách đặt câu hỏi tự nhiên. Không cần biết SQL, không cần hiểu database!

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Ứng Dụng Này Dành Cho Ai?

- **Nhà đầu tư cá nhân** - Tra cứu nhanh thông tin cổ phiếu
- **Sinh viên kinh tế** - Phân tích dữ liệu chứng khoán
- **Nhà phân tích tài chính** - Nghiên cứu xu hướng thị trường
- **Người học AI/ML** - Tìm hiểu ứng dụng thực tế của LangGraph

---

## Tính Năng Nổi Bật

### Hỏi Đáp Thông Minh
- **Tiếng Việt & Tiếng Anh**: "Giá đóng cửa của Apple hôm nay?" hoặc "What was Microsoft's closing price?"
- **Tự động hiểu ý**: Nhận biết tên công ty, ngày tháng, loại dữ liệu cần tra
- **80+ mẫu SQL tích hợp**: Trả lời nhanh các câu hỏi phổ biến
- **AI sinh SQL tự động**: Xử lý câu hỏi phức tạp bằng Gemini AI

### Vẽ Biểu Đồ Tự Động
Chỉ cần nói "vẽ biểu đồ" là có ngay biểu đồ tương tác:
- **Line Chart**: Xu hướng giá theo thời gian + Moving Average
- **Candlestick Chart**: Biểu đồ nến chuyên nghiệp (OHLC + Volume)
- **Comparison Chart**: So sánh nhiều cổ phiếu cùng lúc
- **Volume Chart**: Phân tích khối lượng giao dịch

### Phân Tích Đa Dạng
- **So sánh**: "Apple hay Microsoft có giá cao hơn?"
- **Thống kê**: "Giá trung bình của Boeing trong quý 1/2024?"
- **Xu hướng**: "Biến động giá của Tesla trong năm 2024?"
- **Ranking**: "Top 3 công ty tăng trưởng mạnh nhất?"

### Giao Diện Thân Thiện
- **Chat interface** đơn giản, dễ sử dụng
- **Lịch sử hội thoại** lưu tất cả câu hỏi và trả lời
- **Hiển thị SQL** (tùy chọn) để bạn học hỏi
- **Export biểu đồ** dưới dạng PNG/SVG

---

## Yêu Cầu Hệ Thống

### Phần Cứng
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Ổ cứng**: 500MB dung lượng trống
- **Internet**: Cần kết nối để sử dụng Gemini AI

### Phần Mềm
- **Python**: Phiên bản 3.8 trở lên
- **Hệ điều hành**: Windows, macOS, hoặc Linux
- **Trình duyệt**: Chrome, Firefox, Edge, Safari (bản mới nhất)

### API Key (Miễn Phí)
- **Google Gemini API**: Đăng ký miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## Hướng Dẫn Cài Đặt (5 Phút)

### Bước 1: Tải Code
```bash
# Clone repository
git clone https://github.com/your-repo/langgraph.git
cd langgraph

# Hoặc tải file ZIP và giải nén
```

### Bước 2: Cài Đặt Python Environment
```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1

# macOS/Linux:
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### Bước 3: Cấu Hình API Key

1. **Lấy API Key miễn phí:**
   - Truy cập: https://aistudio.google.com/app/apikey
   - Đăng nhập bằng tài khoản Google
   - Nhấn "Create API Key" và copy key

2. **Tạo file `.env`:**
   
   Tạo file `.env` trong thư mục gốc với nội dung:
   ```env
   GEMINI_API_KEY=AIzaSy...your_key_here
   GOOGLE_API_KEY=AIzaSy...your_key_here
   ```
   
   *(Bạn có thể dùng cùng một key cho cả hai)*

### Bước 4: Khởi Tạo Database
```bash
# Tạo SQLite database từ dữ liệu CSV
python db/init_db.py
```

**Kết quả mong đợi:**
```
Database created successfully at db/djia.db
Loaded 30 companies
Loaded 25000+ price records
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

### Ví Dụ Câu Hỏi

#### Câu Hỏi Cơ Bản
```
Giá đóng cửa của Apple ngày 15/01/2024?
What was Microsoft's closing price on March 15, 2024?
Giá mở cửa của Boeing hôm nay?
```

#### So Sánh Công Ty
```
Ai có giá cao hơn: Apple hay Microsoft ngày 2024-01-15?
Which company had a higher closing price on July 1, 2024: Boeing or Disney?
So sánh giá đóng cửa của Tesla và Apple
```

#### Thống Kê & Phân Tích
```
Giá trung bình của Microsoft trong quý 1/2024?
What was the average closing price of Boeing from January to March 2024?
Tổng khối lượng giao dịch của Apple trong năm 2024?
Công ty nào có giá cao nhất ngày 2024-01-15?
```

#### Vẽ Biểu Đồ (Chỉ cần thêm "vẽ" hoặc "draw")
```
Vẽ biểu đồ giá Apple trong tháng 3/2024
Draw a chart for Microsoft in Q1 2024
Vẽ biểu đồ nến cho Boeing trong năm 2024
Show me the price trend of Tesla in 2024
```

#### Câu Hỏi Về Cổ Tức
```
Ngày nào Apple trả cổ tức trong năm 2024?
On which dates in 2024 did Microsoft pay dividends?
Tổng cổ tức của Boeing trong năm 2024?
```

### Các Tab Trong Ứng Dụng

#### Tab 1: Chat (Hỏi Đáp)
- Nhập câu hỏi tự nhiên
- Xem câu trả lời ngay lập tức
- Biểu đồ tương tác (có thể zoom, pan, export)
- Lịch sử hội thoại được lưu

#### Tab 2: SQL Runner (Nâng Cao)
- Chạy SQL trực tiếp nếu bạn biết SQL
- Xem cấu trúc database
- Thử nghiệm các query phức tạp

### Hiểu Kết Quả Trả Về

Mỗi câu trả lời bao gồm:

1. **Câu Trả Lời Ngắn Gọn**
   ```
   185.92
   ```

2. **Biểu Đồ Tương Tác** (nếu yêu cầu)
   - Có thể zoom in/out
   - Hover để xem chi tiết
   - Export as PNG

3. **SQL Đã Chạy** (Click expander để xem)
   ```sql
   SELECT close FROM prices 
   WHERE ticker = 'AAPL' AND date = '2024-01-15';
   ```

4. **Bảng Dữ Liệu** (Click expander để xem)
   ```
       close
   0   185.92
   ```

5. **Ghi Chú**
   ```
   Đã sử dụng SQL mẫu (nhanh)
   hoặc
   SQL được sinh bởi Gemini AI
   ```

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

## Câu Hỏi Thường Gặp (FAQ)

### 1. Ứng dụng có miễn phí không?
**Có!** Code hoàn toàn miễn phí. Gemini API cũng miễn phí với giới hạn 15 requests/phút.

### 2. Tôi không biết Python, có dùng được không?
**Có!** Chỉ cần cài Python và chạy theo hướng dẫn. Không cần biết code.

### 3. Dữ liệu có cập nhật real-time không?
**Không.** Dữ liệu trong file CSV cố định. Để cập nhật, bạn cần import CSV mới.

### 4. Có thể thêm công ty khác không?
**Có!** Thêm vào file CSV và chạy lại `python db/init_db.py`.

### 5. Tôi muốn hỏi về cổ phiếu Việt Nam được không?
**Có!** Chỉ cần chuẩn bị dữ liệu CSV theo format tương tự.

### 6. Ứng dụng có lưu lịch sử câu hỏi không?
**Có!** Lịch sử được lưu trong session (xóa khi đóng tab hoặc nhấn "Xóa hội thoại").

### 7. Tôi có thể export biểu đồ không?
**Có!** Hover vào biểu đồ và nhấn icon camera để chọn định dạng PNG hoặc SVG.

### 8. API key có bị lộ không?
**An toàn!** Key lưu trong file `.env` (không được commit lên Git).

---

## Xử Lý Lỗi Thường Gặp

### Lỗi: "ModuleNotFoundError"
**Nguyên nhân:** Chưa cài đặt thư viện

**Giải pháp:**
```bash
# Kiểm tra virtual environment đã kích hoạt chưa
# Phải thấy (.venv) ở đầu dòng lệnh

# Cài lại thư viện
pip install -r requirements.txt
```

### Lỗi: "API Key not found"
**Nguyên nhân:** Chưa tạo file `.env` hoặc sai format

**Giải pháp:**
```bash
# Kiểm tra file .env có tồn tại
dir .env       # Windows
ls .env        # macOS/Linux

# Xem nội dung
type .env      # Windows
cat .env       # macOS/Linux

# File phải có nội dung:
# GEMINI_API_KEY=your_key_here
```

### Lỗi: "Database not found"
**Nguyên nhân:** Chưa khởi tạo database

**Giải pháp:**
```bash
python db/init_db.py
```

### Lỗi: "Port 8501 already in use"
**Nguyên nhân:** Đã có Streamlit chạy rồi

**Giải pháp:**
```bash
# Chạy trên port khác
streamlit run app/main.py --server.port 8502
```

### Lỗi: "429 Quota exceeded"
**Nguyên nhân:** Vượt giới hạn API miễn phí

**Giải pháp:**
- Đợi 1 phút và thử lại
- Hoặc tạo API key mới với tài khoản Google khác

---

## Tài Nguyên Học Tập

### Cho Người Dùng
- **README.md** (file này) - Hướng dẫn sử dụng
- Video demo: *(link YouTube nếu có)*

### Cho Developers
- **CODE_GUIDE.md** - Hướng dẫn đọc hiểu code chi tiết
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## Đóng Góp & Hỗ Trợ

### Báo Lỗi
Nếu gặp lỗi, vui lòng tạo issue trên GitHub với:
- Mô tả lỗi chi tiết
- Screenshot (nếu có)
- Steps để reproduce lỗi

### Đóng Góp Code
Pull requests luôn được chào đón! Vui lòng:
1. Fork repository
2. Tạo branch mới
3. Commit changes
4. Tạo pull request

### Liên Hệ
- Email: *(your-email@example.com)*
- GitHub Issues: *(link to issues)*

---

## Giấy Phép

MIT License - Tự do sử dụng, sửa đổi và phân phối.

---

## Lời Cảm Ơn

Dự án này sử dụng các công nghệ mã nguồn mở tuyệt vời:
- **LangGraph** - Multi-agent orchestration
- **Streamlit** - Web interface
- **Plotly** - Interactive charts
- **Google Gemini** - AI capabilities
- **SQLite** - Database

---

## Bắt Đầu Ngay!

```bash
# Clone code
git clone https://github.com/your-repo/langgraph.git
cd langgraph

# Cài đặt
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# Cấu hình API key
# Tạo file .env với GEMINI_API_KEY=your_key

# Khởi tạo database
python db/init_db.py

# Chạy ứng dụng
streamlit run app/main.py
```

**Truy cập:** http://localhost:8501

**Và bắt đầu hỏi đáp ngay!**

---

<div align="center">

**Nếu thấy hữu ích, đừng quên Star repo này nhé!**

Made with Python + AI

</div>
