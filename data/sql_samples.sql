-- FACTUAL, EASY

-- MẪU CÂU HỎI: Giá đóng cửa của {company} vào {date}
-- EN: What was the closing price of {company} on {date}?
-- FIELDS: answer=close
SELECT close
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Giá mở cửa của {company} vào {date}
-- EN: What was the opening price of {company} on {date}?
-- FIELDS: answer=open
SELECT open
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Giá cao nhất của {company} vào {date}
-- EN: What was the highest price {company} reached on {date}?
-- FIELDS: answer=high
SELECT high
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Giá thấp nhất của {company} vào {date}
-- EN: What was the lowest price {company} traded at on {date}?
-- FIELDS: answer=low
SELECT low
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Khối lượng giao dịch của {company} vào {date}
-- EN: What was the trading volume of {company} on {date}?
-- FIELDS: answer=volume
SELECT volume
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Cổ tức của {company} vào {date}
-- EN: What was the dividend of {company} on {date}?
-- FIELDS: answer=dividends
SELECT dividends
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: Chia tách cổ phiếu của {company} vào {date}
-- EN: What was the stock split of {company} on {date}?
-- FIELDS: answer=stock_splits
SELECT stock_splits AS stock_splits
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

-- MẪU CÂU HỎI: {company} thuộc ngành (sector) nào?
-- EN: Which sector does {company} belong to?
-- FIELDS: sector
SELECT sector
FROM companies
WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Mã cổ phiếu (ticker symbol) của {company} là gì?
-- EN: What is the ticker symbol for {company}?
-- FIELDS: symbol
SELECT symbol FROM companies WHERE name ILIKE '%' || :company || '%';

-- MẪU CÂU HỎI: Mô tả về {company}?
-- EN: Description about {company}?
-- FIELDS: description
SELECT description FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Quốc gia của {company}?
-- EN: Country of {company}?
-- FIELDS: country
SELECT country FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Ngành công nghiệp của {company}?
-- EN: Industry of {company}?
-- FIELDS: industry
SELECT industry FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Website của {company}?
-- EN: Website of {company}?
-- FIELDS: website
SELECT website FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Mô tả về {company}?
-- EN: Description about {company}?
-- FIELDS: description
SELECT description FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Market cap của {company}?
-- EN: Market cap of {company}?
-- FIELDS: market_cap
SELECT market_cap FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: PE ratio của {company}?
-- EN: PE ratio of {company}?
-- FIELDS: pe_ratio
SELECT pe_ratio FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Dividend yield của {company}?
-- EN: Dividend yield of {company}?
-- FIELDS: dividend_yield
SELECT dividend_yield FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: 52 week high của {company}?
-- EN: 52 week high of {company}?
-- FIELDS: week_52_high
SELECT week_52_high FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: 52 week low của {company}?
-- EN: 52 week low of {company}?
-- FIELDS: week_52_low
SELECT week_52_low FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Dividends của {company}?
-- EN: Dividends of {company}?
-- FIELDS: dividends
SELECT dividends FROM companies WHERE symbol = :ticker;

-- MẪU CÂU HỎI: Stock splits của {company}?
-- EN: Stock splits of {company}?
-- FIELDS: stock_splits
SELECT stock_splits FROM companies WHERE symbol = :ticker;

--------------------------------
-- FACTUAL, MEDIUM

-- MẪU CÂU HỎI: Giá đóng cửa cao nhất của {company} trong {year}, và khi nào?
-- EN: What was the highest closing price of {company} in {year}, and when?
-- FIELDS: date, max_close
SELECT date, close AS max_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
ORDER BY close DESC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá đóng cửa thấp nhất của {company} trong {year}, và ngày nào?
-- EN: What was the lowest closing price of {company} in {year}, and on what date?
-- FIELDS: date, min_close
SELECT date, close AS min_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
ORDER BY close ASC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá mở cửa cao nhất của {company} trong {year}, và khi nào?
-- EN: What was the highest opening price of {company} in {year}, and when?
-- FIELDS: date, max_open
SELECT date, open AS max_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
ORDER BY open DESC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá mở cửa thấp nhất của {company} trong {year}, và ngày nào?
-- EN: What was the lowest opening price of {company} in {year}, and on what date?
-- FIELDS: date, min_open
SELECT date, open AS min_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
ORDER BY open ASC, date ASC
LIMIT 1;

-- MẪU CÂU HỎI: {company} trả bao nhiêu lần cổ tức trong {year}?
-- EN: How many dividends did {company} pay in {year}?
-- FIELDS: dividends_count
SELECT COUNT(*) AS dividends_count
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND dividends > 0;

-- MẪU CÂU HỎI: Cổ tức trên mỗi cổ phần {company} đã trả vào {date} là bao nhiêu?
-- EN: What dividend per share did {company} pay on {date}?
-- FIELDS: dividend_per_share
SELECT dividends AS dividend_per_share
FROM prices
WHERE ticker = :ticker
  AND date = CAST(:date AS DATE);

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
  AND TO_CHAR(date, 'YYYY') = :year
  AND dividends > 0
ORDER BY date ASC;

-- -----------------------------
-- COMPARATIVE, EASY

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower closing price, {company_a} or {company_b}?
-- FIELDS: a_close, b_close
WITH a AS (
  SELECT close AS a_close FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT close AS b_close FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_close, b.b_close FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower opening price, {company_a} or {company_b}?
-- FIELDS: a_open, b_open
WITH a AS (
  SELECT open AS a_open FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT open AS b_open FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_open, b.b_open FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday high, {company_a} or {company_b}?
-- FIELDS: a_high, b_high
WITH a AS (
  SELECT high AS a_high FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT high AS b_high FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_high, b.b_high FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower intraday low, {company_a} or {company_b}?
-- FIELDS: a_low, b_low
WITH a AS (
  SELECT low AS a_low FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT low AS b_low FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_low, b.b_low FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which company had a higher/lower volume, {company_a} or {company_b}?
-- FIELDS: a_volume, b_volume
WITH a AS (
  SELECT volume AS a_volume FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT volume AS b_volume FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_volume, b.b_volume FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower dividend, {company_a} or {company_b}?
-- FIELDS: a_dividends, b_dividends
WITH a AS (
  SELECT dividends AS a_dividends FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT dividends AS b_dividends FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_dividends, b.b_dividends FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cổ phiếu cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower stock split ratio, {company_a} or {company_b}?
-- FIELDS: a_stock_splits, b_stock_splits
WITH a AS (
  SELECT stock_splits AS a_stock_splits FROM prices WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT stock_splits AS b_stock_splits FROM prices WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_stock_splits, b.b_stock_splits FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có market cap cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower market cap, {company_a} or {company_b}?
-- FIELDS: a_market_cap, b_market_cap
WITH a AS (
  SELECT market_cap AS a_market_cap FROM companies WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT market_cap AS b_market_cap FROM companies WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_market_cap, b.b_market_cap FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có PE ratio cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower PE ratio, {company_a} or {company_b}?
-- FIELDS: a_pe_ratio, b_pe_ratio
WITH a AS (
  SELECT pe_ratio AS a_pe_ratio FROM companies WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT pe_ratio AS b_pe_ratio FROM companies WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_pe_ratio, b.b_pe_ratio FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có Dividend yield cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower Dividend yield, {company_a} or {company_b}?
-- FIELDS: a_dividend_yield, b_dividend_yield
WITH a AS (
  SELECT dividend_yield AS a_dividend_yield FROM companies WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT dividend_yield AS b_dividend_yield FROM companies WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_dividend_yield, b.b_dividend_yield FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có 52 week high cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower 52 week high, {company_a} or {company_b}?
-- FIELDS: a_52_week_high, b_52_week_high
WITH a AS (
  SELECT week_52_high AS a_52_week_high FROM companies WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT week_52_high AS b_52_week_high FROM companies WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_52_week_high, b.b_52_week_high FROM a CROSS JOIN b;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có 52 week low cao/thấp hơn: {company_a} hay {company_b}?
-- EN: On {date}, which had a higher/lower 52 week low, {company_a} or {company_b}?
-- FIELDS: a_52_week_low, b_52_week_low
WITH a AS (
  SELECT week_52_low AS a_52_week_low FROM companies WHERE ticker = :ticker_a AND date = CAST(:date AS DATE)
), b AS (
  SELECT week_52_low AS b_52_week_low FROM companies WHERE ticker = :ticker_b AND date = CAST(:date AS DATE)
)
SELECT a.a_52_week_low, b.b_52_week_low FROM a CROSS JOIN b;

-- -----------------------------
-- COMPARATIVE, MEDIUM

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa thấp nhất?
-- EN: Which company had the lowest closing price on {date}?
-- FIELDS: company, close
SELECT c.name AS company, p.close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.close ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá đóng cửa cao nhất?
-- EN: Which company had the highest closing price on {date}?
-- FIELDS: company, close
SELECT c.name AS company, p.close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.close DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa thấp nhất?
-- EN: Which company had the lowest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.open ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá mở cửa cao nhất?
-- EN: Which company had the highest opening price on {date}?
-- FIELDS: company, open
SELECT c.name AS company, p.open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.open DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.high ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá cao nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday high on {date}?
-- FIELDS: company, high
SELECT c.name AS company, p.high
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.high DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày thấp nhất?
-- EN: Which company had the lowest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.low ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có giá thấp nhất trong ngày cao nhất?
-- EN: Which company had the highest intraday low on {date}?
-- FIELDS: company, low
SELECT c.name AS company, p.low
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.low DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng thấp nhất?
-- EN: Which company had the lowest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.volume ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có khối lượng cao nhất?
-- EN: Which company had the highest volume on {date}?
-- FIELDS: company, volume
SELECT c.name AS company, p.volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.volume DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức thấp nhất?
-- EN: Which company had the lowest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.dividends ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có cổ tức cao nhất?
-- EN: Which company had the highest dividend on {date}?
-- FIELDS: company, dividends
SELECT c.name AS company, p.dividends
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY p.dividends DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách thấp nhất?
-- EN: Which company had the lowest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p.stock_splits AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY stock_splits ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có tỷ lệ chia tách cao nhất?
-- EN: Which company had the highest stock split ratio on {date}?
-- FIELDS: company, stock_splits
SELECT c.name AS company, p.stock_splits AS stock_splits
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE p.date = CAST(:date AS DATE)
ORDER BY stock_splits DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có market cap cao nhất?
-- EN: Which company had the highest market cap on {date}?
-- FIELDS: company, market_cap
SELECT c.name AS company, c.market_cap AS market_cap
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.market_cap DESC, c.name ASC
LIMIT 1;


-- MẪU CÂU HỎI: Vào {date}, công ty nào có market cap thấp nhất?
-- EN: Which company had the lowest market cap on {date}?
-- FIELDS: company, market_cap
SELECT c.name AS company, c.market_cap AS market_cap
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.market_cap ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có PE ratio cao nhất?
-- EN: Which company had the highest PE ratio on {date}?
-- FIELDS: company, pe_ratio
SELECT c.name AS company, c.pe_ratio AS pe_ratio
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.pe_ratio DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có PE ratio thấp nhất?
-- EN: Which company had the lowest PE ratio on {date}?
-- FIELDS: company, pe_ratio
SELECT c.name AS company, c.pe_ratio AS pe_ratio
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.pe_ratio ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có Dividend yield cao nhất?
-- EN: Which company had the highest Dividend yield on {date}?
-- FIELDS: company, dividend_yield
SELECT c.name AS company, c.dividend_yield AS dividend_yield
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.dividend_yield DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có Dividend yield thấp nhất?
-- EN: Which company had the lowest Dividend yield on {date}?
-- FIELDS: company, dividend_yield
SELECT c.name AS company, c.dividend_yield AS dividend_yield
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.dividend_yield ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có 52 week high cao nhất?
-- EN: Which company had the highest 52 week high on {date}?
-- FIELDS: company, week_52_high
SELECT c.name AS company, c.week_52_high AS week_52_high
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.week_52_high DESC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Vào {date}, công ty nào có 52 week high thấp nhất?
-- EN: Which company had the lowest 52 week high on {date}?
-- FIELDS: company, week_52_high
SELECT c.name AS company, c.week_52_high AS week_52_high
FROM companies c
WHERE c.date = CAST(:date AS DATE)
ORDER BY c.week_52_high ASC, c.name ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có khối lượng giao dịch trung bình cao nhất trong {year}?
-- EN: Which company had the highest average trading volume in {year}?
-- FIELDS: company, ticker, avg_volume
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.volume), 0) AS avg_volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_volume DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có khối lượng giao dịch trung bình thấp nhất trong {year}?
-- EN: Which company had the lowest average trading volume in {year}?
-- FIELDS: company, ticker, avg_volume
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.volume), 0) AS avg_volume
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_volume ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có giá mở cửa trung bình cao nhất trong {year}?
-- EN: Which company had the highest average opening price in {year}?
-- FIELDS: company, ticker, avg_open
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.open), 0) AS avg_open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_open DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có giá mở cửa trung bình thấp nhất trong {year}?
-- EN: Which company had the lowest average opening price in {year}?
-- FIELDS: company, ticker, avg_open
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.open), 0) AS avg_open
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_open ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có giá đóng cửa trung bình trong ngày cao nhất trong {year}?
-- EN: Which company had the highest average closing price in {year}?
-- FIELDS: company, ticker, avg_close
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.close), 0) AS avg_close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_close DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có giá đóng cửa trung bình trong ngày thấp nhất trong {year}?
-- EN: Which company had the lowest average closing price in {year}?
-- FIELDS: company, ticker, avg_close
SELECT
  c.name AS company,
  p.ticker,
  ROUND(AVG(p.close), 0) AS avg_close
FROM prices p
JOIN companies c ON c.symbol = p.ticker
WHERE TO_CHAR(p.date, 'YYYY') = :year
GROUP BY p.ticker, c.name
ORDER BY avg_close ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức giảm phần trăm trong ngày lớn nhất trong {year}?
-- EN: Which company experienced the highest single-day percentage drop in {year}?
-- FIELDS: company, ticker, max_drop
WITH daily_changes AS (
  SELECT
    ticker,
    date,
    (close - open) * 100.0 / open AS percentage_change
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
min_changes AS (
  SELECT
    ticker,
    MIN(percentage_change) AS max_drop
  FROM daily_changes
  GROUP BY ticker
)
SELECT
  c.name AS company,
  m.ticker,
  ROUND(m.max_drop, 2) AS max_drop
FROM min_changes m
JOIN companies c ON c.symbol = m.ticker
ORDER BY max_drop ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức giảm phần trăm trong ngày nhỏ nhất trong {year}?
-- EN: Which company experienced the lowest single-day percentage drop in {year}?
-- FIELDS: company, ticker, max_drop
WITH daily_changes AS (
  SELECT
    ticker,
    date,
    (close - open) * 100.0 / open AS percentage_change
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
max_changes AS (
  SELECT
    ticker,
    MAX(percentage_change) AS max_drop
  FROM daily_changes
  GROUP BY ticker
)
SELECT
  c.name AS company,
  m.ticker,
  ROUND(m.max_drop, 2) AS max_drop
FROM max_changes m
JOIN companies c ON c.symbol = m.ticker
ORDER BY max_drop DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức tăng phần trăm trong ngày lớn nhất trong {year}?
-- EN: Which company experienced the highest single-day percentage gain in {year}?
-- FIELDS: company, ticker, max_gain
WITH daily_changes AS (
  SELECT
    ticker,
    date,
    (close - open) * 100.0 / open AS percentage_change
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
max_changes AS (
  SELECT
    ticker,
    MAX(percentage_change) AS max_gain
  FROM daily_changes
  GROUP BY ticker
)
SELECT
  c.name AS company,
  m.ticker,
  ROUND(m.max_gain, 2) AS max_gain
FROM max_changes m
JOIN companies c ON c.symbol = m.ticker
ORDER BY max_gain DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức tăng phần trăm trong ngày nhỏ nhất trong {year}?
-- EN: Which company experienced the lowest single-day percentage gain in {year}?
-- FIELDS: company, ticker, max_gain
WITH daily_changes AS (
  SELECT
    ticker,
    date,
    (close - open) * 100.0 / open AS percentage_change
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
min_changes AS (
  SELECT
    ticker,
    MIN(percentage_change) AS max_gain
  FROM daily_changes
  GROUP BY ticker
)
SELECT
  c.name AS company,
  m.ticker,
  ROUND(m.max_gain, 2) AS max_gain
FROM min_changes m
JOIN companies c ON c.symbol = m.ticker
ORDER BY max_gain ASC
LIMIT 1;

--------------------------------
-- COMPARATIVE, HARD

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
  WHERE TO_CHAR(date, 'YYYY') = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING
    MAX(CASE WHEN rn_asc = 1 THEN close END) IS NOT NULL
    AND MAX(CASE WHEN rn_desc = 1 THEN close END) IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND((last_close - first_close) / first_close * 100, 2) AS percentage_change
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY percentage_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có tỷ lệ giảm giá cổ phiếu lớn nhất trong {year}?
-- EN: Which company had the largest percentage decline in stock price during {year}?
-- FIELDS: company, percentage_decline
WITH daily_closes AS (
  SELECT
    ticker,
    date,
    close,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date ASC) AS rn_asc,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn_desc
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING
    MAX(CASE WHEN rn_asc = 1 THEN close END) IS NOT NULL
    AND MAX(CASE WHEN rn_desc = 1 THEN close END) IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND((last_close - first_close) / first_close * 100, 2) AS percentage_decline
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY percentage_decline ASC     
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
  WHERE TO_CHAR(date, 'YYYY') = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING
    MAX(CASE WHEN rn_asc = 1 THEN close END) IS NOT NULL
    AND MAX(CASE WHEN rn_desc = 1 THEN close END) IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND(last_close - first_close, 2) AS absolute_change
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY absolute_change DESC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức giảm giá tuyệt đối lớn nhất (theo USD) trong {year}?
-- EN: Which company had the largest absolute decrease in closing price (in dollars) during {year}?
-- FIELDS: company, absolute_decrease
WITH daily_closes AS (
  SELECT
    ticker,
    date,
    close,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date ASC) AS rn_asc,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn_desc
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING
    MAX(CASE WHEN rn_asc = 1 THEN close END) IS NOT NULL
    AND MAX(CASE WHEN rn_desc = 1 THEN close END) IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND(first_close - last_close, 2) AS absolute_decrease
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY absolute_decrease ASC
LIMIT 1;

-- MẪU CÂU HỎI: Công ty nào có mức giảm giá tuyệt đối lớn nhất (theo USD) trong {year}?
-- EN: Which company had the largest absolute decrease in closing price (in dollars) during {year}?
-- FIELDS: company, absolute_decrease
WITH daily_closes AS (
  SELECT
    ticker,
    date,
    close,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date ASC) AS rn_asc,
    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn_desc
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
),
bounds AS (
  SELECT
    ticker,
    MAX(CASE WHEN rn_asc = 1 THEN close END) AS first_close,
    MAX(CASE WHEN rn_desc = 1 THEN close END) AS last_close
  FROM daily_closes
  GROUP BY ticker
  HAVING
    MAX(CASE WHEN rn_asc = 1 THEN close END) IS NOT NULL
    AND MAX(CASE WHEN rn_desc = 1 THEN close END) IS NOT NULL
)
SELECT
  c.name AS company,
  ROUND(first_close - last_close, 2) AS absolute_decrease
FROM bounds b
JOIN companies c ON c.symbol = b.ticker
ORDER BY absolute_decrease ASC
LIMIT 1;

-- MẪU CÂU HỎI: Giá đóng cửa của {company} thay đổi bao nhiêu USD từ {start_date} đến {end_date}?
-- EN: By how many dollars did {company}'s closing price change from {start_date} to {end_date}?
-- FIELDS: price_change
WITH start_price AS (
  SELECT close AS start_close FROM prices WHERE ticker = :ticker AND date = CAST(:start_date AS DATE)
), end_price AS (
  SELECT close AS end_close FROM prices WHERE ticker = :ticker AND date = CAST(:end_date AS DATE)
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
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') = :month;

-- MẪU CÂU HỎI: Giá mở cửa trung bình của {company} trong {month} {year}?
-- EN: What was the average opening price of {company} in {month} {year}?
-- FIELDS: avg_open
SELECT ROUND(AVG(open), 2) AS avg_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') = :month;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong quý {quarter} {year}?
-- EN: What was the average closing price of {company} during Q{quarter} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND CASE 
    WHEN :quarter = 1 THEN TO_CHAR(date, 'MM') IN ('01', '02', '03')
    WHEN :quarter = 2 THEN TO_CHAR(date, 'MM') IN ('04', '05', '06')
    WHEN :quarter = 3 THEN TO_CHAR(date, 'MM') IN ('07', '08', '09')
    WHEN :quarter = 4 THEN TO_CHAR(date, 'MM') IN ('10', '11', '12')
  END;

-- MẪU CÂU HỎI: Giá mở cửa trung bình của {company} trong quý {quarter} {year}?
-- EN: What was the average opening price of {company} during Q{quarter} {year}?
-- FIELDS: avg_open
SELECT ROUND(AVG(open), 2) AS avg_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND CASE 
    WHEN :quarter = 1 THEN TO_CHAR(date, 'MM') IN ('01', '02', '03')
    WHEN :quarter = 2 THEN TO_CHAR(date, 'MM') IN ('04', '05', '06')
    WHEN :quarter = 3 THEN TO_CHAR(date, 'MM') IN ('07', '08', '09')
    WHEN :quarter = 4 THEN TO_CHAR(date, 'MM') IN ('10', '11', '12')
  END;

-- MẪU CÂU HỎI: Khối lượng giao dịch trung bình hàng ngày của {company} trong {year}?
-- EN: What was the average daily trading volume of {company} in {year}?
-- FIELDS: avg_volume
SELECT ROUND(AVG(volume), 0) AS avg_volume
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: {company} tăng giá bao nhiêu phần trăm trong {year}?
-- EN: By what percentage did {company}'s stock price increase in {year}?
-- FIELDS: percentage_increase
WITH first_day AS (
  SELECT close AS start_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date ASC
  LIMIT 1
),
last_day AS (
  SELECT close AS end_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date DESC
  LIMIT 1
)
SELECT ROUND((end_price - start_price) / start_price * 100, 2) AS percentage_increase
FROM first_day, last_day;

-- MẪU CÂU HỎI: {company} giảm giá bao nhiêu phần trăm trong {year}?
-- EN: By what percentage did {company}'s stock price decrease in {year}?
-- FIELDS: percentage_decrease
WITH first_day AS (
  SELECT close AS start_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date ASC
  LIMIT 1
),
last_day AS (
  SELECT close AS end_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date DESC
  LIMIT 1
)
SELECT ROUND((start_price - end_price) / start_price * 100, 2) AS percentage_decrease
FROM first_day, last_day;

-- MẪU CÂU HỎI: {company} tăng giá bao nhiêu phần trăm trong {year}?
-- EN: By what percentage did {company}'s stock price increase in {year}?
-- FIELDS: percentage_increase
WITH first_day AS (
  SELECT close AS start_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date ASC
  LIMIT 1
),
last_day AS (
  SELECT close AS end_price
  FROM prices
  WHERE ticker = :ticker
    AND date >= (:year || '-01-01')::date
    AND date <  ((:year + 1) || '-01-01')::date
  ORDER BY date DESC
  LIMIT 1
)
SELECT ROUND((end_price - start_price) / start_price * 100, 2) AS percentage_increase
FROM first_day, last_day;

-- -- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong nửa đầu {year}?
-- EN: What was the average closing price of {company} in the first half of {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') IN ('01', '02', '03', '04', '05', '06');

-- MẪU CÂU HỎI: Giá mở cửa trung bình của {company} trong nửa đầu {year}?
-- EN: What was the average opening price of {company} in the first half of {year}?
-- FIELDS: avg_open
SELECT ROUND(AVG(open), 2) AS avg_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') IN ('01', '02', '03', '04', '05', '06');

-- MẪU CÂU HỎI: Giá mở cửa trung bình của {company} trong nửa cuối {year}?
-- EN: What was the average opening price of {company} in the second half of {year}?
-- FIELDS: avg_open
SELECT ROUND(AVG(open), 2) AS avg_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') IN ('07', '08', '09', '10', '11', '12');



-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} trong nửa cuối {year}?
-- EN: What was the average closing price of {company} in the second half of {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') IN ('07', '08', '09', '10', '11', '12');

-- MẪU CÂU HỎI: Đường trung bình động 7 phiên của giá đóng cửa {company} tại {date} là bao nhiêu?
-- EN: What was the 7-session moving average closing price of {company} on {date}?
-- FIELDS: moving_avg_close
WITH last_7_sessions AS (
  SELECT close
  FROM prices
  WHERE ticker = :ticker
    AND date <= CAST(:date AS DATE)
  ORDER BY date DESC
  LIMIT 7
)
SELECT ROUND(AVG(close), 2) AS moving_avg_close
FROM last_7_sessions;

-- MẪU CÂU HỎI: Đường trung bình động 30 phiên của giá đóng cửa {company} tại {date} là bao nhiêu?
-- EN: What was the 30-session moving average closing price of {company} on {date}?
-- FIELDS: moving_avg_close
WITH last_30_sessions AS (
  SELECT close
  FROM prices
  WHERE ticker = :ticker
    AND date <= CAST(:date AS DATE)
  ORDER BY date DESC
  LIMIT 30
)
SELECT ROUND(AVG(close), 2) AS moving_avg_close
FROM last_30_sessions;

-- MẪU CÂU HỎI: Tuần nào trong {year} {company} có khối lượng giao dịch cao nhất và khối lượng đó là bao nhiêu?
-- EN: What was {company}'s highest weekly trading volume in {year}, and which week was it?
-- FIELDS: week_start, total_volume
WITH weekly_volume AS (
  SELECT
    DATE_TRUNC('week', date)::date AS week_start,
    SUM(volume) AS total_volume
  FROM prices
  WHERE ticker = :ticker
    AND TO_CHAR(date, 'YYYY') = :year
  GROUP BY DATE_TRUNC('week', date)
)
SELECT
  week_start,
  total_volume
FROM weekly_volume
ORDER BY total_volume DESC
LIMIT 1;

-- -----------------------------
-- ANALYTICAL, MEDIUM

-- MẪU CÂU HỎI: Tổng khối lượng giao dịch của {company} trong {year} là bao nhiêu?
-- EN: What was the total trading volume for {company} in {year}?
-- FIELDS: total_volume
SELECT SUM(volume) AS total_volume
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: Giá đóng cửa trung bình của {company} từ tháng {start_month} đến tháng {end_month} năm {year}?
-- EN: What was the average closing price of {company} from {start_month} to {end_month} {year}?
-- FIELDS: avg_close
SELECT ROUND(AVG(close), 2) AS avg_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') BETWEEN :start_month AND :end_month;

-- MẪU CÂU HỎI: Giá mở cửa trung bình của {company} từ tháng {start_month} đến tháng {end_month} năm {year}?
-- EN: What was the average opening price of {company} from {start_month} to {end_month} {year}?
-- FIELDS: avg_open
SELECT ROUND(AVG(open), 2) AS avg_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year
  AND TO_CHAR(date, 'MM') BETWEEN :start_month AND :end_month;

-- MẪU CÂU HỎI: Lợi nhuận tích lũy của {company} từ {start_date} đến {end_date} là bao nhiêu?
-- EN: What was the cumulative return of {company} from {start_date} to {end_date}?
-- FIELDS: cumulative_return
WITH start_price AS (
  SELECT close AS start_close
  FROM prices
  WHERE ticker = :ticker
    AND date >= CAST(:start_date AS DATE)
  ORDER BY date ASC
  LIMIT 1
), end_price AS (
  SELECT close AS end_close
  FROM prices
  WHERE ticker = :ticker
    AND date <= CAST(:end_date AS DATE)
  ORDER BY date DESC
  LIMIT 1
)
SELECT ROUND((end_close - start_close) / start_close * 100, 2) AS cumulative_return
FROM start_price, end_price;

-- MẪU CÂU HỎI: Lợi suất cổ tức trung bình của toàn bộ DJIA trong {year} là bao nhiêu?
-- EN: What was the average dividend yield for the DJIA as a whole in {year}?
-- FIELDS: avg_dividend_yield
WITH company_yields AS (
  SELECT
    ticker,
    SUM(dividends) / NULLIF(SUM(close), 0) AS dividend_yield
  FROM prices
  WHERE TO_CHAR(date, 'YYYY') = :year
  GROUP BY ticker
)
SELECT ROUND(AVG(dividend_yield) * 100, 2) AS avg_dividend_yield
FROM company_yields
WHERE dividend_yield IS NOT NULL;

-- MẪU CÂU HỎI: Median giá đóng cửa của {company} trong {year} là bao nhiêu?
-- EN: What was the median closing price of {company} in {year}?
-- FIELDS: median_close
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY close) AS median_close
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: Median giá mở cửa của {company} trong {year} là bao nhiêu?
-- EN: What was the median opening price of {company} in {year}?
-- FIELDS: median_open
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY open) AS median_open
FROM prices
WHERE ticker = :ticker
  AND TO_CHAR(date, 'YYYY') = :year;

-- MẪU CÂU HỎI: CAGR của {company} từ {start_date} đến {end_date} là bao nhiêu?
-- EN: What was the compound annual growth rate (CAGR) of {company} from {start_date} to {end_date}?
-- FIELDS: cagr
WITH start_price AS (
  SELECT close AS start_close
  FROM prices
  WHERE ticker = :ticker
    AND date >= CAST(:start_date AS DATE)
  ORDER BY date ASC
  LIMIT 1
), end_price AS (
  SELECT close AS end_close
  FROM prices
  WHERE ticker = :ticker
    AND date <= CAST(:end_date AS DATE)
  ORDER BY date DESC
  LIMIT 1
)
SELECT ROUND((POWER(end_close / start_close, 1.0 / :years) - 1) * 100, 2) AS cagr
FROM start_price, end_price;