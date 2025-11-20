# 🚀 HƯỚNG DẪN CHẠY NHANH

## Bước 1: Cài đặt dependencies (Đã hoàn thành ✅)

Dependencies đã được cài đặt! Các package đã cài:
- ✅ streamlit
- ✅ plotly  
- ✅ langgraph
- ✅ pandas
- ✅ google-generativeai
- ✅ và các package khác...

## Bước 2: Thiết lập API Key

Tạo file `.env` trong thư mục `/workspace/`:

```bash
# Tạo file .env
nano .env

# Hoặc echo trực tiếp:
echo "GEMINI_API_KEY=your_api_key_here" > .env
echo "GOOGLE_API_KEY=your_api_key_here" >> .env
```

**Lưu ý**: Thay `your_api_key_here` bằng API key thực của bạn từ Google AI Studio.

## Bước 3: Khởi tạo Database (nếu chưa có)

```bash
cd /workspace
python3 db/init_db.py
```

## Bước 4: Chạy ứng dụng

### Cách 1: Sử dụng script tự động
```bash
cd /workspace
./run_app.sh
```

### Cách 2: Chạy trực tiếp
```bash
cd /workspace
export PATH=$PATH:/home/ubuntu/.local/bin
streamlit run app/main.py
```

### Cách 3: Với Python module
```bash
cd /workspace
export PATH=$PATH:/home/ubuntu/.local/bin
python3 -m streamlit run app/main.py
```

## Bước 5: Truy cập ứng dụng

Mở trình duyệt và vào:
```
http://localhost:8501
```

## 💡 Ví dụ câu hỏi để test

### Câu hỏi đơn giản:
```
Giá đóng cửa của Apple vào ngày 15/03/2024?
What was the closing price of Microsoft on March 15, 2024?
```

### Vẽ biểu đồ:
```
Vẽ biểu đồ giá Apple trong tháng 3/2024
Draw a chart of Microsoft stock in Q1 2024
Vẽ biểu đồ nến Boeing trong năm 2024
So sánh xu hướng giá Apple và Microsoft
```

### Phân tích thống kê:
```
Độ lệch chuẩn của giá Apple trong 2024?
What was the volatility of Microsoft in 2024?
Top 3 companies by total return in 2024
Correlation between Apple and Microsoft in 2024?
```

## ⚠️ Lưu ý

1. **Nếu lỗi "command not found: streamlit"**:
   ```bash
   export PATH=$PATH:/home/ubuntu/.local/bin
   ```

2. **Nếu lỗi "No module named 'google.genai'"**:
   ```bash
   pip install --user google-generativeai
   ```

3. **Nếu database không tồn tại**:
   ```bash
   python3 db/init_db.py
   ```

4. **Để dừng server**: Nhấn `Ctrl+C` trong terminal

## 🆘 Cần trợ giúp?

- Xem tài liệu chi tiết: [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)
- Xem tính năng mới: [ENHANCEMENTS.md](ENHANCEMENTS.md)
- Xem tổng kết: [SUMMARY.md](SUMMARY.md)

## 🎉 Tính năng nổi bật

✨ **Auto Chart Generation** - Tự động vẽ biểu đồ khi được yêu cầu
📊 **4 Chart Types** - Line, Candlestick, Comparison, Volume  
🧮 **Advanced Analytics** - Volatility, Correlation, CAGR, Median
🏆 **Multi-Company** - Rankings, comparisons, statistics
🌐 **Bilingual** - Tiếng Việt + English

---

**Chúc bạn sử dụng Agent DJIA hiệu quả! 🚀**
