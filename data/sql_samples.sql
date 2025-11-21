-- FACTUAL, EASY

-- MẪU CÂU HỎI: Giá đóng cửa của {company} vào {date}
-- EN: What was the closing price of {company} on {date}?
-- FIELDS: answer=close
SELECT close
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Giá mở cửa của {company} vào {date}
-- EN: What was the opening price of {company} on {date}?
-- FIELDS: answer=open
SELECT open
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Giá cao nhất của {company} vào {date}
-- EN: What was the highest price {company} reached on {date}?
-- FIELDS: answer=high
SELECT high
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Giá thấp nhất của {company} vào {date}
-- EN: What was the lowest price {company} traded at on {date}?
-- FIELDS: answer=low
SELECT low
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Khối lượng giao dịch của {company} vào {date}
-- EN: What was the trading volume of {company} on {date}?
-- FIELDS: answer=volume
SELECT volume
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Cổ tức của {company} vào {date}
-- EN: What was the dividend of {company} on {date}?
-- FIELDS: answer=dividends
SELECT dividends
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: Chia tách cổ phiếu của {company} vào {date}
-- EN: What was the stock split of {company} on {date}?
-- FIELDS: answer=stock_splits
SELECT "Stock Splits" AS stock_splits
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);
--------------------------------
-- FACTUAL, MEDIUM

-- MẪU CÂU HỎI: Giá đóng cửa cao nhất của {company} trong {year}, và khi nào?
-- EN: What was the highest closing price of {company} in {year}, and when?
-- FIELDS: date, max_close
SELECT date, close AS max_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
ORDER BY close DESC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá đóng cửa thấp nhất của {company} trong {year}, và ngày nào?
-- EN: What was the lowest closing price of {company} in {year}, and on what date?
-- FIELDS: date, min_close
SELECT date, close AS min_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
ORDER BY close ASC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá mở cửa cao nhất của {company} trong {year}, và khi nào?
-- EN: What was the highest opening price of {company} in {year}, and when?
-- FIELDS: date, max_open
SELECT date, open AS max_open
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
ORDER BY open DESC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá mở cửa thấp nhất của {company} trong {year}, và ngày nào?
-- EN: What was the lowest opening price of {company} in {year}, and on what date?
-- FIELDS: date, min_open
SELECT date, open AS min_open
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
ORDER BY open ASC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: {company} trả bao nhiêu lần cổ tức trong {year}?
-- EN: How many dividends did {company} pay in {year}?
-- FIELDS: dividends_count
SELECT COUNT(*) AS dividends_count
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND dividends > 0;

-- MẪU CÂU HỎI: Cổ tức trên mỗi cổ phần {company} đã trả vào {date} là bao nhiêu?
-- EN: What dividend per share did {company} pay on {date}?
-- FIELDS: dividend_per_share
SELECT dividends AS dividend_per_share
FROM prices
WHERE ticker = :ticker
  AND date(date) = date(:date);

-- MẪU CÂU HỎI: {company} thực hiện chia tách cổ phiếu khi nào và tỷ lệ bao nhiêu?
-- EN: On what date did {company} execute a stock split, and what was the split ratio?
-- FIELDS: date, split_ratio
SELECT date, "Stock Splits" AS split_ratio
FROM prices
WHERE ticker = :ticker
  AND "Stock Splits" > 0
ORDER BY date ASC;

-- MẪU CÂU HỎI: Trong {year}, {company} trả cổ tức vào những ngày nào và bao nhiêu?
-- EN: On which dates in {year} did {company} pay dividends, and what were the amounts?
-- FIELDS: date, dividend
SELECT date, dividends AS dividend
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND dividends > 0
ORDER BY date ASC;

-- -----------------------------
-- COMPARATIVE, EASY

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower closing price, {company_a} or {company_b}?
-- FIELDS: a_close, b_close
WITH a AS (
  SELECT close AS a_close FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT close AS b_close FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_close, b.b_close FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower opening price, {company_a} or {company_b}?
-- FIELDS: a_open, b_open
WITH a AS (
  SELECT open AS a_open FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT open AS b_open FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_open, b.b_open FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday high, {company_a} or {company_b}?
-- FIELDS: a_high, b_high
WITH a AS (
  SELECT high AS a_high FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT high AS b_high FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_high, b.b_high FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday low, {company_a} or {company_b}?
-- FIELDS: a_low, b_low
WITH a AS (
  SELECT low AS a_low FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT low AS b_low FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_low, b.b_low FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower volume, {company_a} or {company_b}?
-- FIELDS: a_volume, b_volume
WITH a AS (
  SELECT volume AS a_volume FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT volume AS b_volume FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_volume, b.b_volume FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower dividend, {company_a} or {company_b}?
-- FIELDS: a_dividends, b_dividends
WITH a AS (
  SELECT dividends AS a_dividends FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT dividends AS b_dividends FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_dividends, b.b_dividends FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cổ phiếu cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower stock split ratio, {company_a} or {company_b}?
-- FIELDS: a_stock_splits, b_stock_splits
WITH a AS (
  SELECT "Stock Splits" AS a_stock_splits FROM prices WHERE ticker = :ticker_a AND date(date) = date(:date)
), b AS (
  SELECT "Stock Splits" AS b_stock_splits FROM prices WHERE ticker = :ticker_b AND date(date) = date(:date)
)
SELECT a.a_stock_splits, b.b_stock_splits FROM a CROSS JOIN b;

-- -----------------------------
-- COMPARATIVE, MEDIUM

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa thấp nhất?
-- EN: Which company had the lowest closing price on {date}?
-- FIELDS: company, close
SELECT c.name AS company, p.close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.close ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao nhất?
-- EN: Which company had the highest closing price on {date}?
-- FIELDS: company, close
SELECT c.name AS company, p.close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.close DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa thấp nhất?
-- EN: Which company had the lowest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.open ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao nhất?
-- EN: Which company had the highest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.open DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.high ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.high DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.low ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.low DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng thấp nhất?
-- EN: Which company had the lowest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.volume ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao nhất?
-- EN: Which company had the highest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.volume DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức thấp nhất?
-- EN: Which company had the lowest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.dividends ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao nhất?
-- EN: Which company had the highest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY p.dividends DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách thấp nhất?
-- EN: Which company had the lowest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p."Stock Splits" AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY stock_splits ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cao nhất?
-- EN: Which company had the highest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p."Stock Splits" AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = date(:date)
ORDER BY stock_splits DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có tỷ lệ tăng giá cổ phiếu lớn nhất trong {year}?
-- EN: Which company had the largest percentage increase in its stock price during {year}?
-- FIELDS: company, percentage_change
WITH daily_closes AS (
  SELECT
    ticker,
    date,
    close,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date ASC) AS rn_asc,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn_desc
  FROM prices
  WHERE strftime('%Y', date) = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING first_close IS NOT NULL AND last_close IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND((last_close - first_close) / first_close * 100, 2) AS percentage_change
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY percentage_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức tăng giá tuyệt đối lớn nhất (theo USD) trong {year}?
-- EN: Which company had the largest absolute increase in closing price (in dollars) during {year}?
-- FIELDS: company, absolute_change
WITH daily_closes AS (
  SELECT
    ticker,
    date,
    close,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date ASC) AS rn_asc,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn_desc
  FROM prices
  WHERE strftime('%Y', date) = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING first_close IS NOT NULL AND last_close IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND(last_close - first_close, 2) AS absolute_change
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY absolute_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có tỷ lệ giảm giá cổ phiếu lớn nhất trong {year}?
-- EN: Which company had the largest percentage decline in stock price during {year}?
-- FIELDS: company, percentage_decline
WITH price_changes AS (
  SELECT 
    ticker,
    (MIN(close) - MAX(close)) / MAX(close) * 100 AS percentage_decline
  FROM prices 
  WHERE strftime('%Y', date) = :year
  GROUP BY ticker
)
SELECT c.name AS company, ROUND(pc.percentage_decline, 2) AS percentage_decline
FROM price_changes pc
JOIN companies c ON c.symbol = pc.ticker
ORDER BY pc.percentage_decline DESC
LIMIT 1;

-- MẪU CÂU HỎI: Giá đóng cửa của {company} thay đổi bao nhiêu USD từ {start_date} đến {end_date}?
-- EN: By how many dollars did {company}'s closing price change from {start_date} to {end_date}?
-- FIELDS: price_change
WITH start_price AS (
  SELECT close AS start_close FROM prices WHERE ticker = :ticker AND date(date) = DATE(:start_date)
), end_price AS (
  SELECT close AS end_close FROM prices WHERE ticker = :ticker AND date(date) = DATE(:end_date)
)
SELECT ROUND(end_price.end_close - start_price.start_close, 2) AS price_change
FROM start_price CROSS JOIN end_price;

-- -----------------------------
-- ANALYTICAL, EASY

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong {month} {year}?
-- EN: What was the average closing price of {company} in {month} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND strftime('%m', date) = :month;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong quý {quarter} {year}?
-- EN: What was the average closing price of {company} during Q{quarter} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND CASE 
    WHEN :quarter = 1 THEN strftime('%m', date) IN ('01', '02', '03')
    WHEN :quarter = 2 THEN strftime('%m', date) IN ('04', '05', '06')
    WHEN :quarter = 3 THEN strftime('%m', date) IN ('07', '08', '09')
    WHEN :quarter = 4 THEN strftime('%m', date) IN ('10', '11', '12')
  END;

-- MẪU CÂU HỎI: Khối lượng giao dịch trung bình hàng ngày của {company} trong {year}?
-- EN: What was the average daily trading volume of {company} in {year}?
-- FIELDS: avg_volume
SELECT ROUND(AVG(volume), 0) AS avg_volume
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year;

-- MẪU CÂU HỎI: {company} tăng giá bao nhiêu phần trăm trong {year}?
-- EN: By what percentage did {company}'s stock price increase in {year}?
-- FIELDS: percentage_increase
WITH year_prices AS (
  SELECT MIN(close) AS start_price, MAX(close) AS end_price
  FROM prices
  WHERE ticker = :ticker AND strftime('%Y', date) = :year
)
SELECT ROUND((end_price - start_price) / start_price * 100, 2) AS percentage_increase
FROM year_prices;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong nửa cuối {year}?
-- EN: What was the average closing price of {company} in the second half of {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND strftime('%m', date) IN ('07', '08', '09', '10', '11', '12');

-- -----------------------------
-- ANALYTICAL, MEDIUM

-- MẪU CÂU HỎI: Tổng khối lượng giao dịch của {company} trong {year} là bao nhiêu?
-- EN: What was the total trading volume for {company} in {year}?
-- FIELDS: total_volume
SELECT SUM(volume) AS total_volume
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong quý {quarter} {year} là bao nhiêu?
-- EN: What was the average closing price of {company} during Q{quarter} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND CASE 
    WHEN :quarter = 1 THEN strftime('%m', date) IN ('01', '02', '03')
    WHEN :quarter = 2 THEN strftime('%m', date) IN ('04', '05', '06')
    WHEN :quarter = 3 THEN strftime('%m', date) IN ('07', '08', '09')
    WHEN :quarter = 4 THEN strftime('%m', date) IN ('10', '11', '12')
  END;



-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} từ tháng {start_month} đến tháng {end_month} năm {year}?
-- EN: What was the average closing price of {company} from {start_month} to {end_month} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND strftime('%m', date) BETWEEN :start_month AND :end_month;

-- -----------------------------
-- FACTUAL, EASY (COMPANIES METADATA)

-- MẪU CÂU HỎI: {company} thuộc ngành (sector) nào?
-- EN: Which sector does {company} belong to?
-- FIELDS: sector
SELECT sector
FROM companies
WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Mã cổ phiếu (ticker symbol) của {company} là gì?
-- EN: What is the ticker symbol for {company}?
-- FIELDS: symbol
SELECT :ticker AS symbol;

-- -----------------------------
-- COMPARATIVE, EASY (YEARLY)

-- MẪU CÂU HỎI: Trong {year}, cổ tức trên mỗi cổ phiếu của ai cao hơn: {company_a} hay {company_b}?
-- EN: Which company had higher dividends per share in {year}, {company_a} or {company_b}?
-- FIELDS: a_dividends_per_share, b_dividends_per_share
WITH a AS (
  SELECT ROUND(SUM(dividends), 2) AS a_dividends_per_share
  FROM prices
  WHERE ticker = :ticker_a AND strftime('%Y', date) = :year
), b AS (
  SELECT ROUND(SUM(dividends), 2) AS b_dividends_per_share
  FROM prices
  WHERE ticker = :ticker_b AND strftime('%Y', date) = :year
)
SELECT a.a_dividends_per_share, b.b_dividends_per_share FROM a CROSS JOIN b;

-- -----------------------------
-- ANALYTICAL, MEDIUM (INDEX-LEVEL)

-- MẪU CÂU HỎI: Lợi suất cổ tức trung bình của toàn bộ DJIA trong {year} là bao nhiêu?
-- EN: What was the average dividend yield for the DJIA as a whole in {year}?
-- FIELDS: avg_dividend_yield
SELECT ROUND(AVG(dividend_yield), 4) AS avg_dividend_yield
<<<<<<< Current (Your changes)
FROM companies;
=======
FROM yearly_yield;

-- -----------------------------
-- ANALYTICAL, DIFFICULT (ADVANCED ANALYTICS)

-- MẪU CÂU HỎI: Độ lệch chuẩn (standard deviation) của giá đóng cửa {company} trong {year}?
-- EN: What was the standard deviation of {company}'s daily closing prices in {year}?
-- FIELDS: std_dev
WITH stats AS (
  SELECT 
    AVG(close) as mean_close,
    COUNT(*) as n
  FROM prices
  WHERE ticker = :ticker
    AND strftime('%Y', date) = :year
)
SELECT ROUND(SQRT(SUM((close - mean_close) * (close - mean_close)) / (n - 1)), 2) AS std_dev
FROM prices, stats
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year;

-- MẪU CÂU HỎI: Có bao nhiêu ngày giao dịch {company} đóng cửa trên {price}?
-- EN: How many trading days in {year} saw {company}'s closing price above {price}?
-- FIELDS: days_count
SELECT COUNT(*) AS days_count
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
  AND close > :price;

-- MẪU CÂU HỎI: Biến động giá (volatility) hàng ngày của {company} trong {year}?
-- EN: What was the daily volatility of {company} in {year}?
-- FIELDS: daily_volatility
WITH daily_returns AS (
  SELECT 
    date,
    (close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) * 100 AS daily_return
  FROM prices
  WHERE ticker = :ticker
    AND strftime('%Y', date) = :year
),
stats AS (
  SELECT 
    AVG(daily_return) as mean_return,
    COUNT(*) as n
  FROM daily_returns
  WHERE daily_return IS NOT NULL
)
SELECT ROUND(SQRT(SUM((daily_return - mean_return) * (daily_return - mean_return)) / (n - 1)), 2) AS daily_volatility
FROM daily_returns, stats
WHERE daily_return IS NOT NULL;

-- MẪU CÂU HỎI: Tổng lợi nhuận (total return) của {company} trong {year}?
-- EN: Calculate the total return of {company} for {year}
-- FIELDS: total_return_pct
WITH year_prices AS (
  SELECT 
    (SELECT close FROM prices WHERE ticker = :ticker AND strftime('%Y', date) = :year ORDER BY date ASC LIMIT 1) as start_price,
    (SELECT close FROM prices WHERE ticker = :ticker AND strftime('%Y', date) = :year ORDER BY date DESC LIMIT 1) as end_price
)
SELECT ROUND((end_price - start_price) / start_price * 100, 2) AS total_return_pct
FROM year_prices;

-- MẪU CÂU HỎI: Giá trị trung vị (median) của giá đóng cửa {company} trong {year}?
-- EN: Calculate the median closing price of {company} in {year}
-- FIELDS: median_close
WITH ordered_prices AS (
  SELECT 
    close,
    ROW_NUMBER() OVER (ORDER BY close) as rn,
    COUNT(*) OVER () as total
  FROM prices
  WHERE ticker = :ticker
    AND strftime('%Y', date) = :year
)
SELECT 
  ROUND(AVG(close), 2) as median_close
FROM ordered_prices
WHERE rn IN ((total + 1) / 2, (total + 2) / 2);

-- MẪU CÂU HỎI: Moving average 30 ngày của {company} vào {date}?
-- EN: What was the 30-day moving average closing price of {company} on {date}?
-- FIELDS: ma30_close
SELECT ROUND(AVG(close), 2) AS ma30_close
FROM (
  SELECT close
  FROM prices
  WHERE ticker = :ticker
    AND date(date) <= date(:date)
  ORDER BY date DESC
  LIMIT 30
);

-- MẪU CÂU HỎI: Tuần nào {company} có khối lượng giao dịch cao nhất trong {year}?
-- EN: What was {company}'s highest weekly trading volume in {year}, and which week was it?
-- FIELDS: week_start, weekly_volume
SELECT 
  date(date, 'weekday 0', '-6 days') as week_start,
  SUM(volume) as weekly_volume
FROM prices
WHERE ticker = :ticker
  AND strftime('%Y', date) = :year
GROUP BY strftime('%W', date)
ORDER BY weekly_volume DESC
LIMIT 1;

-- MẪU CÂU HỎI: Tỷ lệ tăng trưởng kép hàng năm (CAGR) của {company} từ {start_date} đến {end_date}?
-- EN: What was the compound annual growth rate (CAGR) of {company} from {start_date} to {end_date}?
-- FIELDS: cagr_pct
WITH price_range AS (
  SELECT 
    (SELECT close FROM prices WHERE ticker = :ticker AND date(date) = date(:start_date)) as start_price,
    (SELECT close FROM prices WHERE ticker = :ticker AND date(date) = date(:end_date)) as end_price,
    (julianday(:end_date) - julianday(:start_date)) / 365.25 as years
)
SELECT ROUND((POWER(end_price / start_price, 1.0 / years) - 1) * 100, 2) AS cagr_pct
FROM price_range;

-- -----------------------------
-- COMPARATIVE, DIFFICULT (MULTI-COMPANY ANALYTICS)

-- MẪU CÂU HỎI: Xếp hạng top 3 công ty theo tổng lợi nhuận trong {year}
-- EN: Rank the top 3 companies by total return in {year}
-- FIELDS: company, total_return_pct
WITH returns AS (
  SELECT 
    ticker,
    ((MAX(close) - MIN(close)) / MIN(close)) * 100 as total_return_pct
  FROM prices
  WHERE strftime('%Y', date) = :year
  GROUP BY ticker
)
SELECT 
  c.name as company,
  ROUND(r.total_return_pct, 2) as total_return_pct
FROM returns r
JOIN companies c ON c.symbol = r.ticker
ORDER BY r.total_return_pct DESC
LIMIT 3;

-- MẪU CÂU HỎI: Công ty nào có khối lượng giao dịch trung bình cao nhất trong {year}?
-- EN: Which company had the highest average trading volume in {year}?
-- FIELDS: company, avg_volume
SELECT 
  c.name as company,
  ROUND(AVG(p.volume), 0) as avg_volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE strftime('%Y', p.date) = :year
GROUP BY p.ticker
ORDER BY avg_volume DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có biến động thấp nhất (standard deviation) trong {year}?
-- EN: Which company had the lowest volatility (standard deviation of daily returns) in {year}?
-- FIELDS: company, volatility
WITH daily_returns AS (
  SELECT 
    ticker,
    date,
    (close - LAG(close) OVER (PARTITION BY ticker ORDER BY date)) / 
     LAG(close) OVER (PARTITION BY ticker ORDER BY date) * 100 AS daily_return
  FROM prices
  WHERE strftime('%Y', date) = :year
),
volatility AS (
  SELECT 
    ticker,
    SQRT(AVG(daily_return * daily_return) - AVG(daily_return) * AVG(daily_return)) as std_dev
  FROM daily_returns
  WHERE daily_return IS NOT NULL
  GROUP BY ticker
)
SELECT 
  c.name as company,
  ROUND(v.std_dev, 2) as volatility
FROM volatility v
JOIN companies c ON c.symbol = v.ticker
ORDER BY v.std_dev ASC
LIMIT 1;

-- MẪU CÂU HỎI: Tương quan (correlation) giữa giá {company_a} và {company_b} trong {year}?
-- EN: What was the correlation between {company_a}'s and {company_b}'s daily returns in {year}?
-- FIELDS: correlation
WITH returns_a AS (
  SELECT 
    date,
    (close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) AS return_a
  FROM prices
  WHERE ticker = :ticker_a
    AND strftime('%Y', date) = :year
),
returns_b AS (
  SELECT 
    date,
    (close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) AS return_b
  FROM prices
  WHERE ticker = :ticker_b
    AND strftime('%Y', date) = :year
),
combined AS (
  SELECT 
    a.return_a,
    b.return_b
  FROM returns_a a
  JOIN returns_b b ON a.date = b.date
  WHERE a.return_a IS NOT NULL AND b.return_b IS NOT NULL
),
stats AS (
  SELECT 
    AVG(return_a) as mean_a,
    AVG(return_b) as mean_b,
    COUNT(*) as n
  FROM combined
)
SELECT 
  ROUND(
    SUM((return_a - mean_a) * (return_b - mean_b)) / 
    (SQRT(SUM((return_a - mean_a) * (return_a - mean_a))) * 
     SQRT(SUM((return_b - mean_b) * (return_b - mean_b)))),
  2) AS correlation
FROM combined, stats;

>>>>>>> Incoming (Background Agent changes)
