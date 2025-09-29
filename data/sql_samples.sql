-- FACTUAL, EASY

-- MẪU CÂU HỎI: Giá đóng cửa của {company} vào {date}
-- EN: What was the closing price of {company} on {date}?
-- FIELDS: answer=close
SELECT close
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Giá mở cửa của {company} vào {date}
-- EN: What was the opening price of {company} on {date}?
-- FIELDS: answer=open
SELECT open
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Giá cao nhất của {company} vào {date}
-- EN: What was the highest price {company} reached on {date}?
-- FIELDS: answer=high
SELECT high
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Giá thấp nhất của {company} vào {date}
-- EN: What was the lowest price {company} traded at on {date}?
-- FIELDS: answer=low
SELECT low
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Khối lượng giao dịch của {company} vào {date}
-- EN: What was the trading volume of {company} on {date}?
-- FIELDS: answer=volume
SELECT volume
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Cổ tức của {company} vào {date}
-- EN: What was the dividend of {company} on {date}?
-- FIELDS: answer=dividends
SELECT dividends
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: Chia tách cổ phiếu của {company} vào {date}
-- EN: What was the stock split of {company} on {date}?
-- FIELDS: answer=stock_splits
SELECT stock_splits
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
  AND to_char(date, 'YYYY') = :year
ORDER BY close DESC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá đóng cửa thấp nhất của {company} trong {year}, và ngày nào?
-- EN: What was the lowest closing price of {company} in {year}, and on what date?
-- FIELDS: date, min_close
SELECT date, close AS min_close
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
ORDER BY close ASC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: {company} trả bao nhiêu lần cổ tức trong {year}?
-- EN: How many dividends did {company} pay in {year}?
-- FIELDS: dividends_count
SELECT COUNT(*) AS dividends_count
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND dividends > 0;

-- MẪU CÂU HỎI: Cổ tức trên mỗi cổ phần {company} đã trả vào {date} là bao nhiêu?
-- EN: What dividend per share did {company} pay on {date}?
-- FIELDS: dividend_per_share
SELECT dividends AS dividend_per_share
FROM prices
WHERE ticker = :ticker
  AND DATE(date) = DATE(:date);

-- MẪU CÂU HỎI: {company} thực hiện chia tách cổ phiếu khi nào và tỷ lệ bao nhiêu?
-- EN: On what date did {company} execute a stock split, and what was the split ratio?
-- FIELDS: date, split_ratio
SELECT date, stock_splits AS split_ratio
FROM prices
WHERE ticker = :ticker
  AND stock_splits > 0
ORDER BY date ASC;

-- MẪU CÂU HỎI: Trong {year}, {company} trả cổ tức vào những ngày nào và bao nhiêu?
-- EN: On which dates in {year} did {company} pay dividends, and what were the amounts?
-- FIELDS: date, dividend
SELECT date, dividends AS dividend
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND dividends > 0
ORDER BY date ASC;

-- -----------------------------
-- COMPARATIVE, EASY

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower closing price, {company_a} or {company_b}?
-- FIELDS: a_close, b_close
WITH a AS (
  SELECT close AS a_close FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT close AS b_close FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_close, b.b_close FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower opening price, {company_a} or {company_b}?
-- FIELDS: a_open, b_open
WITH a AS (
  SELECT open AS a_open FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT open AS b_open FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_open, b.b_open FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday high, {company_a} or {company_b}?
-- FIELDS: a_high, b_high
WITH a AS (
  SELECT high AS a_high FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT high AS b_high FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_high, b.b_high FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday low, {company_a} or {company_b}?
-- FIELDS: a_low, b_low
WITH a AS (
  SELECT low AS a_low FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT low AS b_low FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_low, b.b_low FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower volume, {company_a} or {company_b}?
-- FIELDS: a_volume, b_volume
WITH a AS (
  SELECT volume AS a_volume FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT volume AS b_volume FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_volume, b.b_volume FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower dividend, {company_a} or {company_b}?
-- FIELDS: a_dividends, b_dividends
WITH a AS (
  SELECT dividends AS a_dividends FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT dividends AS b_dividends FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
)
SELECT a.a_dividends, b.b_dividends FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cổ phiếu cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower stock split ratio, {company_a} or {company_b}?
-- FIELDS: a_stock_splits, b_stock_splits
WITH a AS (
  SELECT stock_splits AS a_stock_splits FROM prices WHERE ticker = :ticker_a AND DATE(date) = DATE(:date)
), b AS (
  SELECT stock_splits AS b_stock_splits FROM prices WHERE ticker = :ticker_b AND DATE(date) = DATE(:date)
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
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.close ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao nhất?
-- EN: Which company had the highest closing price on {date}?
-- FIELDS: company, close
SELECT c.name AS company, p.close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.close DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa thấp nhất?
-- EN: Which company had the lowest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.open ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao nhất?
-- EN: Which company had the highest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.open DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.high ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.high DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.low ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.low DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng thấp nhất?
-- EN: Which company had the lowest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.volume ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao nhất?
-- EN: Which company had the highest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.volume DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức thấp nhất?
-- EN: Which company had the lowest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.dividends ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao nhất?
-- EN: Which company had the highest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.dividends DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách thấp nhất?
-- EN: Which company had the lowest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p.stock_splits AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.stock_splits ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cao nhất?
-- EN: Which company had the highest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p.stock_splits AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE DATE(p.date) = DATE(:date)
ORDER BY p.stock_splits DESC, c.name ASC
LIMIT 1;

-- -----------------------------
-- COMPARATIVE, DIFFICULT

-- MẪU CÂU HỎI: Công ty nào có tỷ lệ tăng giá cổ phiếu lớn nhất trong {year}?
-- EN: Which company had the largest percentage increase in its stock price during {year}?
-- FIELDS: company, percentage_change
WITH price_changes AS (
  SELECT 
    ticker,
    (MAX(close) - MIN(close)) / MIN(close) * 100 AS percentage_change
  FROM prices 
  WHERE to_char(date, 'YYYY') = :year
  GROUP BY ticker
)
SELECT c.name AS company, ROUND(pc.percentage_change, 2) AS percentage_change
FROM price_changes pc
JOIN companies c ON c.symbol = pc.ticker
ORDER BY pc.percentage_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức tăng giá tuyệt đối lớn nhất (theo USD) trong {year}?
-- EN: Which company had the largest absolute increase in closing price (in dollars) during {year}?
-- FIELDS: company, absolute_change
WITH price_changes AS (
  SELECT 
    ticker,
    MAX(close) - MIN(close) AS absolute_change
  FROM prices 
  WHERE to_char(date, 'YYYY') = :year
  GROUP BY ticker
)
SELECT c.name AS company, ROUND(pc.absolute_change, 2) AS absolute_change
FROM price_changes pc
JOIN companies c ON c.symbol = pc.ticker
ORDER BY pc.absolute_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có tỷ lệ giảm giá cổ phiếu lớn nhất trong {year}?
-- EN: Which company had the largest percentage decline in stock price during {year}?
-- FIELDS: company, percentage_decline
WITH price_changes AS (
  SELECT 
    ticker,
    (MIN(close) - MAX(close)) / MAX(close) * 100 AS percentage_decline
  FROM prices 
  WHERE to_char(date, 'YYYY') = :year
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
  SELECT close AS start_close FROM prices WHERE ticker = :ticker AND DATE(date) = DATE(:start_date)
), end_price AS (
  SELECT close AS end_close FROM prices WHERE ticker = :ticker AND DATE(date) = DATE(:end_date)
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
  AND to_char(date, 'YYYY') = :year
  AND to_char(date, 'MM') = :month;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong quý {quarter} {year}?
-- EN: What was the average closing price of {company} during Q{quarter} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND CASE 
    WHEN :quarter = 1 THEN to_char(date, 'MM') IN ('01', '02', '03')
    WHEN :quarter = 2 THEN to_char(date, 'MM') IN ('04', '05', '06')
    WHEN :quarter = 3 THEN to_char(date, 'MM') IN ('07', '08', '09')
    WHEN :quarter = 4 THEN to_char(date, 'MM') IN ('10', '11', '12')
  END;

-- MẪU CÂU HỎI: Khối lượng giao dịch trung bình hàng ngày của {company} trong {year}?
-- EN: What was the average daily trading volume of {company} in {year}?
-- FIELDS: avg_volume
SELECT ROUND(AVG(volume), 0) AS avg_volume
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: {company} tăng giá bao nhiêu phần trăm trong {year}?
-- EN: By what percentage did {company}'s stock price increase in {year}?
-- FIELDS: percentage_increase
WITH year_prices AS (
  SELECT MIN(close) AS start_price, MAX(close) AS end_price
  FROM prices
  WHERE ticker = :ticker AND to_char(date, 'YYYY') = :year
)
SELECT ROUND((end_price - start_price) / start_price * 100, 2) AS percentage_increase
FROM year_prices;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong nửa cuối {year}?
-- EN: What was the average closing price of {company} in the second half of {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND to_char(date, 'MM') IN ('07', '08', '09', '10', '11', '12');

-- -----------------------------
-- ANALYTICAL, MEDIUM

-- MẪU CÂU HỎI: Tổng khối lượng giao dịch của {company} trong {year} là bao nhiêu?
-- EN: What was the total trading volume for {company} in {year}?
-- FIELDS: total_volume
SELECT SUM(volume) AS total_volume
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong quý {quarter} {year} là bao nhiêu?
-- EN: What was the average closing price of {company} during Q{quarter} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND CASE 
    WHEN :quarter = 1 THEN to_char(date, 'MM') IN ('01', '02', '03')
    WHEN :quarter = 2 THEN to_char(date, 'MM') IN ('04', '05', '06')
    WHEN :quarter = 3 THEN to_char(date, 'MM') IN ('07', '08', '09')
    WHEN :quarter = 4 THEN to_char(date, 'MM') IN ('10', '11', '12')
  END;



-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} từ tháng {start_month} đến tháng {end_month} năm {year}?
-- EN: What was the average closing price of {company} from {start_month} to {end_month} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND to_char(date, 'YYYY') = :year
  AND to_char(date, 'MM') BETWEEN :start_month AND :end_month;

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
FROM companies;
