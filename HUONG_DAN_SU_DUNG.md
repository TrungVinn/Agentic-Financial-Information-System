# HƯỚNG DẪN SỬ DỤNG AGENT DJIA NÂNG CAP

## 📋 Tổng quan

Agent DJIA đã được nâng cấp với nhiều tính năng mới:
- ✅ Trả lời câu hỏi phức tạp hơn
- ✅ Tự động vẽ biểu đồ giá khi được yêu cầu
- ✅ Phân tích thống kê nâng cao
- ✅ So sánh nhiều công ty
- ✅ Phân tích xu hướng và biến động

## 🚀 Cài đặt và Chạy

### 1. Cài đặt thư viện (nếu chưa có)
```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng
```bash
streamlit run app/main.py
```

### 3. Truy cập
Mở trình duyệt và vào: `http://localhost:8501`

## 💡 Các loại câu hỏi mà Agent có thể trả lời

### 1. Câu hỏi cơ bản về giá (như trước)

**Ví dụ:**
```
- Giá đóng cửa của Apple vào ngày 15/03/2024 là bao nhiêu?
- Giá mở cửa của Microsoft vào ngày 1/1/2024?
- Khối lượng giao dịch của Boeing vào ngày 5/3/2025?
```

### 2. Câu hỏi yêu cầu VẼ BIỂU ĐỒ ⭐ (MỚI)

#### 2.1. Biểu đồ đường (Line Chart)
```
- Vẽ biểu đồ giá Apple trong tháng 3/2024
- Hiển thị xu hướng giá Microsoft trong năm 2024
- Cho tôi xem biểu đồ giá Boeing trong Q1 2025
- Draw a chart of Apple stock price in 2024
```

**Kết quả:** Biểu đồ đường với giá đóng cửa + đường trung bình động 20 ngày (MA20)

#### 2.2. Biểu đồ nến (Candlestick Chart)
```
- Vẽ biểu đồ nến Microsoft từ tháng 1 đến tháng 3 năm 2024
- Hiển thị biểu đồ nến Apple trong Q1 2024
- Show me candlestick chart for Boeing in March 2024
```

**Kết quả:** Biểu đồ nến OHLC + biểu đồ khối lượng giao dịch

#### 2.3. Biểu đồ so sánh (Comparison Chart)
```
- So sánh xu hướng giá Apple và Microsoft trong 2024
- Vẽ biểu đồ so sánh giá Boeing và Disney
- Compare Apple vs Microsoft stock performance
```

**Kết quả:** Biểu đồ so sánh chuẩn hóa theo phần trăm thay đổi

#### 2.4. Biểu đồ khối lượng (Volume Chart)
```
- Vẽ biểu đồ khối lượng giao dịch Apple trong 2024
- Hiển thị volume chart của Microsoft
- Show trading volume chart for Boeing
```

**Kết quả:** Biểu đồ cột khối lượng + đường trung bình động

### 3. Câu hỏi PHÂN TÍCH THỐNG KÊ ⭐ (MỚI)

#### 3.1. Độ lệch chuẩn (Standard Deviation)
```
- Độ lệch chuẩn của giá đóng cửa Apple trong 2024 là bao nhiêu?
- What was the standard deviation of Microsoft's closing prices in 2024?
- Tính độ lệch chuẩn giá Boeing trong năm 2024
```

#### 3.2. Biến động giá (Volatility)
```
- Biến động giá hàng ngày của Apple trong 2024?
- What was the daily volatility of Microsoft in 2024?
- Tính volatility của Boeing trong năm 2024
```

#### 3.3. Giá trị trung vị (Median)
```
- Giá trị trung vị của giá đóng cửa Apple trong 2024?
- Calculate the median closing price of Microsoft in 2024
- Tính median price của Boeing trong 2024
```

#### 3.4. Moving Average (Trung bình động)
```
- Moving average 30 ngày của Apple vào ngày 30/4/2024?
- What was the 30-day moving average of Microsoft on April 30, 2024?
```

#### 3.5. CAGR (Tỷ lệ tăng trưởng kép hàng năm)
```
- CAGR của Microsoft từ 01/01/2023 đến 31/12/2024?
- What was the compound annual growth rate of Apple from Jan 1, 2023 to Dec 31, 2024?
```

#### 3.6. Tương quan (Correlation)
```
- Tương quan giữa giá Apple và Microsoft trong 2024?
- What was the correlation between Apple's and Microsoft's daily returns in 2024?
```

### 4. Câu hỏi SO SÁNH NHIỀU CÔNG TY ⭐ (MỚI)

#### 4.1. Xếp hạng Top/Bottom
```
- Top 3 công ty có lợi nhuận cao nhất trong 2024?
- Rank the top 3 companies by total return in 2024
- 3 công ty có tổng lợi nhuận thấp nhất trong 2024?
```

#### 4.2. Tìm công ty theo tiêu chí
```
- Công ty nào có khối lượng giao dịch trung bình cao nhất trong 2024?
- Which company had the highest average trading volume in 2024?
- Công ty nào có biến động thấp nhất trong 2024?
- Which company had the lowest volatility in 2024?
```

### 5. Câu hỏi TỔNG HỢP (Aggregation)

```
- Giá đóng cửa trung bình của Apple trong tháng 3/2025?
- What was the average closing price of Microsoft during Q1 2025?
- Tổng khối lượng giao dịch của Apple trong 2024?
- What was the total trading volume for Microsoft in 2024?
```

### 6. Câu hỏi PHÂN TÍCH THỜI GIAN

```
- Giá đóng cửa trung bình của Apple từ tháng 7 đến tháng 12 năm 2023?
- What was the average closing price of Boeing from July through December 2023?
- Apple tăng giá bao nhiêu phần trăm trong 2024?
- By what percentage did Microsoft's stock price increase in 2024?
```

## 🎨 Các loại biểu đồ và cách yêu cầu

| Loại biểu đồ | Từ khóa | Ví dụ |
|--------------|---------|--------|
| Line Chart | "vẽ", "draw", "hiển thị", "xu hướng" | Vẽ biểu đồ giá Apple |
| Candlestick | "nến", "candlestick", "OHLC" | Vẽ biểu đồ nến Microsoft |
| Comparison | "so sánh", "compare" | So sánh Apple và Microsoft |
| Volume | "khối lượng", "volume" | Vẽ biểu đồ khối lượng Apple |

## 📊 Các chỉ số thống kê được hỗ trợ

| Chỉ số | Tiếng Việt | Tiếng Anh |
|--------|-----------|-----------|
| Độ lệch chuẩn | Standard deviation | std_dev |
| Biến động | Volatility | volatility |
| Trung vị | Median | median |
| Trung bình động | Moving average | MA |
| CAGR | Tỷ lệ tăng trưởng kép | CAGR |
| Tương quan | Correlation | correlation |
| Tổng lợi nhuận | Total return | total return |

## 🔍 Mẹo sử dụng

### 1. Kết hợp nhiều yêu cầu
```
Vẽ biểu đồ giá Apple trong năm 2024 và cho tôi biết độ lệch chuẩn
```

### 2. Chỉ định khoảng thời gian rõ ràng
```
✅ Tốt: "Giá Apple từ tháng 1 đến tháng 3 năm 2024"
❌ Tránh: "Giá Apple gần đây"
```

### 3. Sử dụng tên công ty hoặc ticker
```
✅ Cả hai đều được:
- "Giá Apple vào ngày..."
- "Giá AAPL vào ngày..."
```

### 4. Câu hỏi bằng tiếng Việt hoặc tiếng Anh
```
✅ Tiếng Việt: "Giá đóng cửa của Apple là bao nhiêu?"
✅ English: "What was the closing price of Apple?"
```

## ⚠️ Lưu ý

1. **Dữ liệu có sẵn**: Chỉ có dữ liệu từ 2023-2025 cho các công ty DJIA
2. **Tên công ty**: Agent hiểu cả tên đầy đủ và tên viết tắt
3. **Định dạng ngày**: Nhiều định dạng được hỗ trợ:
   - `15/03/2024`
   - `March 15, 2024`
   - `2024-03-15`

## 🐛 Khắc phục sự cố

### Biểu đồ không hiển thị?
- Kiểm tra câu hỏi có chứa từ khóa "vẽ", "draw", "biểu đồ", "chart" không
- Đảm bảo có chỉ định công ty và khoảng thời gian

### SQL lỗi?
- Kiểm tra tên công ty có đúng không
- Kiểm tra định dạng ngày tháng

### Kết quả không chính xác?
- Làm rõ câu hỏi hơn
- Chỉ định cụ thể trường dữ liệu (closing price, opening price, etc.)

## 📚 Ví dụ đầy đủ

### Ví dụ 1: Phân tích đơn giản
```
User: Giá đóng cửa của Apple vào ngày 15/03/2024?
Agent: Giá đóng cửa của Apple vào ngày 15/03/2024 là $413.26.
```

### Ví dụ 2: Vẽ biểu đồ
```
User: Vẽ biểu đồ giá Microsoft trong tháng 3/2024
Agent: [Hiển thị biểu đồ đường với giá Microsoft và MA20]
       Đây là biểu đồ giá Microsoft trong tháng 3/2024. 
       Giá dao động từ $405 đến $422...
```

### Ví dụ 3: Phân tích thống kê
```
User: Độ lệch chuẩn của giá Apple trong 2024?
Agent: Độ lệch chuẩn của giá đóng cửa Apple trong năm 2024 là $12.50.
       Điều này cho thấy giá có biến động trung bình...
```

### Ví dụ 4: So sánh công ty
```
User: Top 3 công ty có lợi nhuận cao nhất trong 2024?
Agent: [Hiển thị bảng]
       1. Salesforce: 60.5%
       2. Microsoft: 38.2%
       3. UnitedHealth Group: 32.1%
```

## 🎯 Các tính năng nổi bật

1. ⚡ **Tự động phát hiện**: Agent tự biết khi nào cần vẽ biểu đồ
2. 🎨 **Biểu đồ đẹp**: Sử dụng Plotly cho biểu đồ tương tác
3. 📊 **Phân tích sâu**: Hỗ trợ nhiều chỉ số thống kê
4. 🔄 **Lịch sử chat**: Lưu cả câu trả lời và biểu đồ
5. 🌐 **Đa ngôn ngữ**: Hỗ trợ cả tiếng Việt và tiếng Anh

## 🆘 Cần trợ giúp?

Nếu có vấn đề, xem file `ENHANCEMENTS.md` để biết thêm chi tiết kỹ thuật hoặc tạo issue trên GitHub.

---

**Chúc bạn sử dụng Agent DJIA hiệu quả! 🚀**
