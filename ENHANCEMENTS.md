# DJIA Agent Enhancements

## Tổng quan các cải tiến

Agent DJIA đã được nâng cấp để có thể xử lý các câu hỏi phức tạp hơn và tự động tạo biểu đồ giá khi được yêu cầu.

## 1. Các tính năng mới

### 1.1. Query Planner (Bộ lập kế hoạch truy vấn)
- **File**: `nodes/planner.py`
- **Chức năng**: 
  - Phân tích độ phức tạp của câu hỏi
  - Phát hiện các yêu cầu về biểu đồ
  - Tự động xác định loại biểu đồ phù hợp
  - Tạo kế hoạch thực thi cho câu hỏi phức tạp

- **Các loại độ phức tạp được phát hiện**:
  - Multi-step queries (câu hỏi nhiều bước)
  - Comparison queries (so sánh)
  - Aggregation queries (tổng hợp)
  - Statistical analysis (phân tích thống kê)
  - Time series analysis (phân tích chuỗi thời gian)

### 1.2. Chart Generator (Bộ tạo biểu đồ)
- **File**: `nodes/chart_generator.py`
- **Các loại biểu đồ được hỗ trợ**:
  1. **Line Chart** (Biểu đồ đường): 
     - Hiển thị xu hướng giá theo thời gian
     - Tự động thêm Moving Average 20 ngày
  
  2. **Candlestick Chart** (Biểu đồ nến):
     - Hiển thị OHLC (Open, High, Low, Close)
     - Kèm theo biểu đồ khối lượng giao dịch
     - Màu xanh cho ngày tăng, đỏ cho ngày giảm
  
  3. **Comparison Chart** (Biểu đồ so sánh):
     - So sánh nhiều cổ phiếu cùng lúc
     - Chuẩn hóa theo phần trăm thay đổi
  
  4. **Volume Chart** (Biểu đồ khối lượng):
     - Hiển thị khối lượng giao dịch
     - Tự động thêm Moving Average khối lượng

- **Tự động phát hiện yêu cầu vẽ biểu đồ**:
  - Từ khóa: "vẽ", "draw", "plot", "chart", "biểu đồ"
  - Từ khóa xu hướng: "trend", "xu hướng", "thay đổi", "biến động"

### 1.3. Advanced SQL Templates (Mẫu SQL nâng cao)
- **File**: `data/sql_samples.sql` (đã được mở rộng)
- **Các mẫu SQL mới**:

#### Phân tích thống kê:
- Standard deviation (độ lệch chuẩn)
- Volatility (biến động)
- Median (trung vị)
- Moving averages (đường trung bình động)
- CAGR (tỷ lệ tăng trưởng kép hàng năm)
- Correlation (tương quan giữa 2 cổ phiếu)

#### Phân tích nâng cao:
- Số ngày giao dịch đóng cửa trên một mức giá
- Tổng lợi nhuận (total return)
- Phân tích theo tuần (weekly analysis)
- Top/Bottom ranking theo nhiều tiêu chí

#### Multi-company analytics:
- Xếp hạng công ty theo nhiều tiêu chí
- So sánh volatility giữa các công ty
- Tìm công ty có khối lượng giao dịch cao nhất

### 1.4. Enhanced Workflow
- **File**: `graphs/djia_graph.py`
- **Luồng xử lý mới**:
  ```
  User Question → Plan Query → Match SQL Template → [Generate SQL if needed] 
       → Execute SQL → [Generate Chart if needed] → Summarize Answer
  ```

- **Conditional Routing**:
  - Tự động quyết định có cần sinh SQL bằng LLM không
  - Tự động quyết định có cần vẽ biểu đồ không

### 1.5. Updated UI
- **File**: `app/main.py`
- **Cải tiến giao diện**:
  - Hiển thị biểu đồ tương tác (interactive) với Plotly
  - Lưu và hiển thị biểu đồ trong lịch sử chat
  - Responsive charts (tự động điều chỉnh kích thước)

## 2. Ví dụ sử dụng

### 2.1. Câu hỏi đơn giản (vẫn hoạt động như trước)
```
Q: Giá đóng cửa của Apple vào ngày 15/03/2024 là bao nhiêu?
A: $413.26
```

### 2.2. Câu hỏi yêu cầu vẽ biểu đồ
```
Q: Vẽ biểu đồ giá Apple trong tháng 3/2024
→ Trả về: Line chart với giá Apple và MA20

Q: Vẽ biểu đồ nến Microsoft trong Q1 2024
→ Trả về: Candlestick chart với OHLC và volume

Q: So sánh xu hướng giá của Apple và Microsoft trong 2024
→ Trả về: Comparison chart với 2 đường
```

### 2.3. Câu hỏi phân tích thống kê
```
Q: Độ lệch chuẩn của giá Apple trong 2024 là bao nhiêu?
→ Tính toán standard deviation

Q: Tương quan giữa Apple và Microsoft trong 2024?
→ Tính correlation coefficient

Q: Biến động giá hàng ngày của Boeing trong 2024?
→ Tính daily volatility
```

### 2.4. Câu hỏi phức tạp
```
Q: Top 3 công ty có lợi nhuận cao nhất trong 2024?
→ Xếp hạng và trả về bảng kết quả

Q: Công ty nào có volatility thấp nhất trong 2024?
→ Tính toán và so sánh tất cả công ty

Q: CAGR của Microsoft từ 01/01/2023 đến 31/12/2024?
→ Tính compound annual growth rate
```

## 3. Cấu trúc thư mục mới

```
/workspace/
├── nodes/
│   ├── planner.py                 # NEW: Query planning
│   ├── chart_generator.py         # NEW: Chart generation
│   ├── sql_template_matcher.py
│   ├── sql_llm_generator.py
│   ├── sql_executor.py
│   ├── answer_summarizer.py
│   └── utils.py
├── graphs/
│   └── djia_graph.py             # UPDATED: New workflow
├── app/
│   └── main.py                   # UPDATED: Chart display
├── data/
│   └── sql_samples.sql           # UPDATED: More templates
└── ENHANCEMENTS.md               # NEW: This file
```

## 4. Dependencies mới

Các package đã có sẵn trong `requirements.txt`:
- `plotly>=5.10.0` - Để tạo biểu đồ tương tác
- `pandas>=1.5.0` - Xử lý dữ liệu
- `streamlit>=1.25.0` - UI framework

## 5. Cách chạy

```bash
# 1. Cài đặt dependencies (nếu chưa có)
pip install -r requirements.txt

# 2. Chạy Streamlit app
streamlit run app/main.py

# 3. Truy cập: http://localhost:8501
```

## 6. Kiểm tra tính năng mới

### Test 1: Vẽ biểu đồ cơ bản
```
Input: "Vẽ biểu đồ giá Apple trong năm 2024"
Expected: Line chart với giá Apple và MA20
```

### Test 2: Biểu đồ nến
```
Input: "Vẽ biểu đồ nến Microsoft từ tháng 1 đến tháng 3 năm 2024"
Expected: Candlestick chart với OHLC và volume
```

### Test 3: So sánh
```
Input: "So sánh xu hướng giá Apple và Microsoft trong 2024"
Expected: Comparison chart với 2 đường chuẩn hóa
```

### Test 4: Phân tích thống kê
```
Input: "Độ lệch chuẩn của giá đóng cửa Apple trong 2024?"
Expected: Số liệu statistical với giải thích
```

### Test 5: Multi-company
```
Input: "Top 3 công ty có tổng lợi nhuận cao nhất trong 2024"
Expected: Bảng xếp hạng với 3 công ty
```

## 7. Tính năng nổi bật

1. **Tự động phát hiện intent**: Agent tự động hiểu khi nào cần vẽ biểu đồ
2. **Chọn loại biểu đồ phù hợp**: Tự động chọn line/candlestick/comparison/volume
3. **SQL templates phong phú**: 80+ templates cho nhiều loại câu hỏi
4. **Phân tích thống kê**: Hỗ trợ volatility, correlation, standard deviation
5. **Interactive charts**: Biểu đồ tương tác với Plotly (zoom, pan, hover)
6. **Chat history**: Lưu và hiển thị lại cả câu trả lời và biểu đồ

## 8. Hạn chế và cải tiến tương lai

### Hạn chế hiện tại:
- Chưa hỗ trợ multiple charts trong 1 câu trả lời
- Chưa có export chart (PNG, PDF)
- Chưa có custom chart colors/themes

### Cải tiến tương lai:
- Thêm technical indicators (RSI, MACD, Bollinger Bands)
- Hỗ trợ portfolio analysis
- Real-time data updates
- Custom date range picker
- Export reports (PDF, Excel)

## 9. Troubleshooting

### Lỗi: "Module 'plotly' not found"
```bash
pip install plotly>=5.10.0
```

### Lỗi: Biểu đồ không hiển thị
- Kiểm tra `chart` có được trả về trong result không
- Xem log để debug chart generation

### Lỗi: SQL template không match
- Kiểm tra câu hỏi có đúng format không
- Xem các ví dụ trong `djia_qna.json`

## 10. Liên hệ & Đóng góp

Nếu có vấn đề hoặc đề xuất tính năng mới, vui lòng tạo issue hoặc pull request.
