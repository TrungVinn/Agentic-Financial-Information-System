# 📘 HƯỚNG DẪN ĐỌC VÀ HIỂU CODE

## 🎯 Mục đích document này

Document này giúp bạn hiểu rõ cấu trúc code, luồng hoạt động và cách thức từng component làm việc với nhau trong hệ thống DJIA Multi-Agent.

---

## 📁 CẤU TRÚC PROJECT (Đã cleaned up)

```
D:\KLTN\langgraph\
├── 📁 app/                      # Frontend Streamlit
│   └── main.py                  # Giao diện chat chính
│
├── 📁 nodes/                    # 6 Agents chuyên biệt
│   ├── planner.py               # 🧠 Query Planner
│   ├── sql_template_matcher.py  # 🔍 SQL Template Matcher
│   ├── sql_llm_generator.py     # 🤖 SQL Generator (Gemini AI)
│   ├── sql_executor.py          # ⚙️ SQL Executor
│   ├── chart_generator.py       # 📊 Chart Generator
│   ├── answer_summarizer.py     # 💬 Answer Summarizer
│   └── utils.py                 # 🛠️ Utility functions
│
├── 📁 graphs/                   # LangGraph Workflow
│   └── djia_graph.py            # 🔄 Main workflow orchestration
│
├── 📁 data/                     # Dữ liệu
│   ├── djia_companies_*.csv     # Thông tin 30 công ty DJIA
│   ├── djia_prices_*.csv        # Dữ liệu giá lịch sử
│   └── sql_samples.sql          # 80+ SQL templates
│
├── 📁 db/                       # Database
│   ├── djia.db                  # SQLite database (auto-generated)
│   └── init_db.py               # Script khởi tạo DB
│
├── config.py                    # ⚙️ Cấu hình paths & schema
├── requirements.txt             # 📦 Dependencies
├── README.md                    # 📖 User documentation
├── CODE_GUIDE.md               # 📘 Code documentation (file này)
└── .env                         # 🔐 API keys (tạo thủ công)
```

---

## 🔄 LUỒNG HOẠT ĐỘNG TỔNG QUAN

```
User Question
     ↓
┌────────────────────────────────────────────────────────┐
│  1️⃣ QUERY PLANNER (nodes/planner.py)                  │
│  - Phân tích độ phức tạp câu hỏi                       │
│  - Phát hiện yêu cầu vẽ biểu đồ (CHẶT CHẼ)            │
│  - Tạo execution plan cho câu hỏi phức tạp            │
└────────────────┬───────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────┐
│  2️⃣ SQL TEMPLATE MATCHER (nodes/sql_template_matcher) │
│  - Trích xuất ticker (AAPL, MSFT, ...)                │
│  - Tìm SQL mẫu phù hợp từ 80+ templates               │
│  - Validate bằng LLM nếu cần                          │
└────────────────┬───────────────────────────────────────┘
                 ↓
        ┌────────┴────────┐
        │                 │
     CÓ SQL MẪU?         KHÔNG
        │                 ↓
        │     ┌────────────────────────────────┐
        │     │  3️⃣ SQL GENERATOR (Gemini AI)  │
        │     │  - Sinh SQL mới bằng AI        │
        │     │  - Loại bỏ markdown blocks      │
        │     └────────────┬───────────────────┘
        │                  │
        └──────────────────┴───> 4️⃣ SQL EXECUTOR
                                 (nodes/sql_executor.py)
                                 - Build parameters
                                 - Thực thi SQL
                                 - Trả về DataFrame
                                       ↓
                              ┌────────┴────────┐
                              │                 │
                        CẦN BIỂU ĐỒ?          KHÔNG
                              │                 │
                              ↓                 │
                  ┌────────────────────┐        │
                  │  5️⃣ CHART GENERATOR │        │
                  │  - Line chart       │        │
                  │  - Candlestick      │        │
                  │  - Comparison       │        │
                  └────────┬───────────┘        │
                           │                    │
                           └────────────────────┘
                                       ↓
                           ┌────────────────────┐
                           │  6️⃣ ANSWER SUMMARY  │
                           │  - Tạo câu trả lời │
                           └─────────┬──────────┘
                                     ↓
                              Return Result
```

---

## 📚 CHI TIẾT TỪNG MODULE

### 1️⃣ `config.py` - Cấu hình

**Mục đích:** Định nghĩa paths và database schema

**Các constants quan trọng:**
```python
DB_PATH                    # SQLite database path
DJIA_COMPANIES_CSV        # File CSV thông tin công ty
DJIA_PRICES_CSV           # File CSV dữ liệu giá
SQL_SAMPLES_FILE          # File chứa 80+ SQL templates
```

**Database Schema:**
- `companies`: 30 công ty DJIA (symbol, name, sector, ...)
- `prices`: Dữ liệu giá lịch sử (date, open, high, low, close, volume, ...)

---

### 2️⃣ `nodes/planner.py` - Query Planner

**Mục đích:** Phân tích câu hỏi và lập kế hoạch thực thi

**Functions chính:**

#### `detect_query_complexity(question: str) -> Dict`
Phân tích câu hỏi để xác định:
- `needs_chart`: Có cần vẽ biểu đồ không? (CHỈ khi có yêu cầu RÕ RÀNG)
- `chart_type`: Loại biểu đồ (line/candlestick/volume/comparison)
- `is_comparison`: Câu hỏi so sánh (Apple vs Microsoft)
- `is_aggregation`: Câu hỏi tổng hợp (average, sum, total)
- `is_statistical`: Phân tích thống kê (volatility, correlation)
- `is_multi_step`: Câu hỏi phức tạp nhiều bước

**Từ khóa phát hiện biểu đồ:**
```python
# CHỈ VẼ KHI CÓ:
"vẽ", "draw", "plot", "chart", "graph", "biểu đồ"
"visualize", "show", "display"
"show trend", "hiển thị xu hướng"

# KHÔNG TỰ ĐỘNG VẼ CHO:
"average", "which company", "higher/lower"  # Nếu không có từ khóa trên
```

#### `create_execution_plan(question, complexity) -> List`
Tạo execution plan chi tiết cho câu hỏi phức tạp bằng Gemini AI.

#### `plan_query(state) -> Dict` 
LangGraph Node - Entry point của planner.

---

### 3️⃣ `nodes/sql_template_matcher.py` - SQL Template Matcher

**Mục đích:** Tìm SQL mẫu phù hợp từ 80+ templates

**Functions chính:**

#### `match_sql_template(state) -> Dict`
Main node function:
1. Trích xuất ticker từ câu hỏi (AAPL, MSFT, ...)
2. Tìm SQL mẫu phù hợp bằng heuristic rules
3. Validate bằng LLM nếu cần
4. Trả về SQL và ticker

**Các loại SQL templates:**
- **Factual Easy**: Giá đóng cửa ngày cụ thể
- **Factual Medium**: Highest/lowest price in year
- **Comparative Easy**: So sánh 2 công ty
- **Comparative Medium**: Which company had highest price
- **Analytical Easy**: Average, total, quarter analysis
- **Analytical Medium**: Month ranges, index-level queries

**Company Aliases:**
```python
"apple" → "AAPL"
"microsoft" → "MSFT"
"boeing" → "BA"
# ... và nhiều aliases khác
```

---

### 4️⃣ `nodes/sql_llm_generator.py` - SQL Generator

**Mục đích:** Sinh SQL mới bằng Gemini AI khi không có mẫu

**Functions chính:**

#### `generate_sql_with_llm(question, feedback, analysis_hint) -> str`
Gọi Gemini AI để sinh SQL:
- System prompt hướng dẫn sinh SQL cho **SQLite** (KHÔNG phải PostgreSQL)
- Loại bỏ markdown blocks (```sql ... ```)
- Xử lý feedback để retry khi SQL lỗi

**Cú pháp SQLite quan trọng:**
```sql
-- ✅ ĐÚNG (SQLite)
strftime('%Y', date) = :year
strftime('%m', date) = :month
date(date) = date(:date)

-- ❌ SAI (PostgreSQL)
to_char(date, 'YYYY') = :year  # Lỗi: no such function
DATE(date) = DATE(:date)        # Case-sensitive
```

---

### 5️⃣ `nodes/sql_executor.py` - SQL Executor

**Mục đích:** Thực thi SQL trên SQLite database

**Functions chính:**

#### `build_params(question, ticker, state) -> Dict`
Xây dựng parameters từ câu hỏi:
```python
# Ví dụ input:
question = "What was Apple's closing price on 2024-01-15?"
ticker = "AAPL"

# Output:
{
    "ticker": "AAPL",
    "date": "2024-01-15"
}
```

**Xử lý các patterns:**
- Date: `2024-01-15`, `January 15, 2024`, `15/01/2024`
- Year: `2024`, `in 2024`
- Quarter: `Q1`, `Q2`, `first quarter`, `quý 1`
- Month: `January`, `tháng 1`, `01`
- Comparison: `Apple vs Microsoft`, `AAPL or MSFT`

#### `run_sql(sql, params) -> Tuple[DataFrame, str]`
Thực thi SQL với bind parameters (an toàn, tránh SQL injection):
```python
# SQL với parameters:
sql = "SELECT * FROM prices WHERE ticker = :ticker AND date = :date"
params = {"ticker": "AAPL", "date": "2024-01-15"}

# Execute và trả về:
df, display_sql = run_sql(sql, params)
# display_sql = "SELECT * FROM prices WHERE ticker = 'AAPL' AND date = '2024-01-15'"
```

#### `execute_sql(state) -> Dict`
LangGraph Node - Thực thi SQL và xử lý lỗi.

---

### 6️⃣ `nodes/chart_generator.py` - Chart Generator

**Mục đích:** Tạo biểu đồ tương tác bằng Plotly

**4 loại biểu đồ:**
1. **Line Chart**: Xu hướng giá với Moving Average
2. **Candlestick Chart**: Biểu đồ nến OHLC + Volume
3. **Comparison Chart**: So sánh nhiều cổ phiếu
4. **Volume Chart**: Khối lượng giao dịch

**Functions chính:**

#### `generate_chart(state) -> Dict`
LangGraph Node - Tạo biểu đồ dựa trên:
- `chart_type`: Loại biểu đồ
- `df`: DataFrame dữ liệu
- `ticker`: Mã cổ phiếu

**Tính năng:**
- Responsive, có thể zoom/pan
- Tự động thêm Moving Averages
- Tooltip hiển thị chi tiết
- Export as PNG/SVG

---

### 7️⃣ `nodes/answer_summarizer.py` - Answer Summarizer

**Mục đích:** Tạo câu trả lời tự nhiên từ DataFrame

**Functions chính:**

#### `derive_answer(df) -> str`
Trích xuất câu trả lời ngắn gọn từ DataFrame:
```python
# Input DataFrame:
    close
0   185.92

# Output:
"185.92"
```

#### `summarize_answer(state) -> Dict`
LangGraph Node - Tạo câu trả lời cuối cùng.

---

### 8️⃣ `graphs/djia_graph.py` - Workflow Orchestration

**Mục đích:** Điều phối workflow với LangGraph

**Functions chính:**

#### `build_djia_graph() -> CompiledGraph`
Xây dựng workflow graph với 6 nodes và conditional edges.

**Conditional Edges:**
1. **need_llm**: Có SQL mẫu hay cần sinh mới?
2. **need_chart**: Có cần vẽ biểu đồ hay không?

#### `run_djia_graph(question) -> Dict`
Entry point chính:
```python
result = run_djia_graph("What was Apple's closing price on 2024-01-15?")

# Returns:
{
    "success": True,
    "answer": "The closing price was $185.92",
    "sql": "SELECT close FROM prices WHERE ...",
    "df": DataFrame(...),
    "chart": None,
    "used_sample": True,
    "error": None,
    "workflow": [...],
    "complexity": {...}
}
```

---

### 9️⃣ `app/main.py` - Streamlit Frontend

**Mục đích:** Giao diện chat tương tác

**Features:**
- Chat interface với lịch sử
- Hiển thị SQL đã chạy (trong expander)
- Hiển thị DataFrame kết quả
- Hiển thị biểu đồ tương tác (Plotly)
- SQL Runner tab để chạy SQL trực tiếp

**Main components:**
- `st.chat_input()`: Ô nhập câu hỏi
- `st.chat_message()`: Hiển thị tin nhắn
- `st.plotly_chart()`: Hiển thị biểu đồ
- `st.dataframe()`: Hiển thị bảng dữ liệu
- `st.expander()`: Thu gọn SQL và bảng

---

## 🔧 UTILITIES (`nodes/utils.py`)

**Functions quan trọng:**

### `normalize_text(text) -> str`
Chuẩn hóa text: lowercase + remove extra spaces

### `extract_ticker(question) -> Optional[str]`
Trích xuất ticker từ câu hỏi:
```python
extract_ticker("What was Apple's price?")  # → "AAPL"
extract_ticker("MSFT closing price")       # → "MSFT"
extract_ticker("microsoft stock")          # → "MSFT"
```

### `extract_date_parts(question) -> Dict`
Trích xuất date/year/month:
```python
extract_date_parts("on January 15, 2024")
# → {"date": "2024-01-15", "year": "2024", "month": "01"}
```

### `extract_quarter(question) -> Optional[int]`
Trích xuất quý (1-4):
```python
extract_quarter("in Q1 2024")        # → 1
extract_quarter("first quarter")     # → 1
extract_quarter("quý 2")             # → 2
```

### `extract_date_range(question) -> Tuple`
Trích xuất khoảng ngày:
```python
extract_date_range("from January 1 to March 31, 2024")
# → ("2024-01-01", "2024-03-31")
```

---

## 🚀 LUỒNG XỬ LÝ MỘT CÂU HỎI

### Ví dụ: "What was Apple's closing price on January 15, 2024?"

**1. Query Planner:**
```python
complexity = {
    "needs_chart": False,           # Không có "vẽ", "draw", ...
    "is_comparison": False,
    "is_aggregation": False,
    "is_multi_step": False
}
```

**2. SQL Template Matcher:**
```python
ticker = "AAPL"                    # Từ "Apple"
sql = "SELECT close FROM prices WHERE ticker = :ticker AND date = :date;"
used_sample = True
```

**3. SQL Executor:**
```python
params = {"ticker": "AAPL", "date": "2024-01-15"}
df = pd.DataFrame({"close": [185.92]})
```

**4. Answer Summarizer:**
```python
answer = "185.92"
```

**5. Frontend Display:**
```
💬 User: What was Apple's closing price on January 15, 2024?

🤖 Assistant: 185.92

📄 SQL đã chạy (expandable):
SELECT close FROM prices WHERE ticker = 'AAPL' AND date = '2024-01-15';

📊 Bảng kết quả (expandable):
    close
0   185.92
```

---

## 🎨 DESIGN PATTERNS

### 1. **Multi-Agent Pattern**
Mỗi node là một agent chuyên biệt, độc lập:
- Planner: Phân tích
- Matcher: Tìm kiếm
- Generator: Sáng tạo
- Executor: Thực thi
- Chart: Visualization
- Summarizer: Tổng hợp

### 2. **State Management**
LangGraph quản lý state qua các nodes:
```python
state = {
    "question": "...",
    "ticker": "...",
    "sql": "...",
    "df": DataFrame(...),
    "answer": "...",
    # ... và nhiều keys khác
}
```

### 3. **Fallback Strategy**
Nhiều tầng fallback:
1. SQL Template → LLM Generator
2. Heuristic Rules → LLM Validation
3. Primary value → Default value

### 4. **Error Handling**
```python
try:
    df = run_sql(sql, params)
except Exception as e:
    return {"error": str(e), "df": pd.DataFrame()}
```

---

## 🧪 TESTING

### Chạy test suite:
```bash
python test_enhancements.py
```

### Test cases bao gồm:
- Simple queries
- Chart generation (4 types)
- Statistical analysis
- Multi-company comparisons

---

## 📝 CODING CONVENTIONS

### 1. **Docstrings**
Tất cả functions có docstring với:
- Mô tả mục đích
- Args với types
- Returns với types
- Examples (nếu cần)

### 2. **Type Hints**
```python
def build_params(
    question: str,
    ticker: Optional[str],
    state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    ...
```

### 3. **Comments**
- `# ========== SECTION ==========` cho sections lớn
- `# Comment ngắn` cho logic phức tạp
- Docstrings cho functions

### 4. **Naming**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

---

## 🐛 DEBUGGING TIPS

### 1. **Check workflow steps**
```python
result = run_djia_graph("...")
print(result["workflow"])  # Xem các bước đã chạy
```

### 2. **Check SQL**
```python
print(result["sql"])           # SQL đã chạy
print(result["used_sample"])   # Có dùng mẫu không?
```

### 3. **Check DataFrame**
```python
df = result["df"]
print(df.head())
print(df.columns)
```

### 4. **Check error**
```python
if result["error"]:
    print(result["error"])
```

---

## ⚡ PERFORMANCE TIPS

### 1. **SQL Templates > LLM**
SQL mẫu nhanh hơn gọi LLM ~ 10x

### 2. **Cache API Keys**
Load API key một lần, dùng lại nhiều lần

### 3. **Limit LLM calls**
Chỉ gọi LLM khi:
- Không tìm thấy SQL mẫu
- Cần validation
- Cần execution plan

---

## 🔐 SECURITY

### 1. **SQL Injection Protection**
Luôn dùng bind parameters:
```python
# ✅ AN TOÀN
df = pd.read_sql_query(sql, conn, params={"ticker": ticker})

# ❌ NGUY HIỂM
df = pd.read_sql_query(f"SELECT * WHERE ticker = '{ticker}'", conn)
```

### 2. **API Key Protection**
- Lưu trong `.env` (không commit)
- Không hardcode trong code
- Không log ra console

---

## 📚 TÀI LIỆU THAM KHẢO

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Plotly**: https://plotly.com/python/
- **Streamlit**: https://docs.streamlit.io/
- **SQLite**: https://www.sqlite.org/docs.html
- **Pandas**: https://pandas.pydata.org/docs/

---

**📌 Lưu ý:** Code đã được optimize và clean up. Tất cả files dư thừa đã được xóa!

