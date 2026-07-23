-- ============================================================================
-- International Debt Statistics — SQL Analysis
-- Learning focus: GROUP BY aggregation, running totals, and comparing values
-- across countries / indicators / regions.
--
-- Schema
--   international_debt(country_name, country_code, indicator_name,
--                       indicator_code, debt)         -- long format, one row
--                                                      -- per country x indicator
--   country_reference(country_code, country_name, region, income_level,
--                      "DT.DOD.DECT.GN.ZS", "DT.DOD.DSTC.ZS", "DT.TDS.DECT.EX.ZS",
--                      gdp_current_usd, gdp_per_capita_usd, population,
--                      total_reserves_usd)
--   debt_history(country_code, country_name, year, debt)  -- total external debt
--                                                          -- (DT.DOD.DECT.CD),
--                                                          -- one row per country x
--                                                          -- year, 1970-2024
--
-- Written for SQLite (as shipped in this repo's international_debt.db) but
-- kept ANSI-SQL-portable -- runs on Postgres/MySQL with no changes beyond
-- optionally swapping ROUND()'s behaviour.
-- ============================================================================


-- 1. How many distinct countries and indicators are in the dataset?
SELECT
    COUNT(DISTINCT country_name) AS distinct_countries,
    COUNT(DISTINCT indicator_code) AS distinct_indicators,
    COUNT(*) AS total_rows
FROM international_debt;


-- 2. Total external debt owed by all countries combined (the headline number).
SELECT
    ROUND(SUM(debt) / 1e12, 2) AS total_external_debt_trillions_usd
FROM international_debt
WHERE indicator_code = 'DT.DOD.DECT.CD';


-- 3. Which single country owes the most, across the headline "total external
--    debt" indicator? (GROUP BY + ORDER BY + LIMIT)
SELECT
    country_name,
    debt AS total_external_debt_usd
FROM international_debt
WHERE indicator_code = 'DT.DOD.DECT.CD'
ORDER BY debt DESC
LIMIT 1;


-- 4. Average debt per indicator, ranked -- shows which *kind* of debt is
--    largest on average across countries (GROUP BY indicator).
SELECT
    indicator_name,
    indicator_code,
    COUNT(*) AS countries_reporting,
    ROUND(AVG(debt) / 1e9, 2) AS avg_debt_billions_usd
FROM international_debt
GROUP BY indicator_name, indicator_code
ORDER BY avg_debt_billions_usd DESC;


-- 5. Most "common" indicator -- the one reported by the most countries
--    (i.e. best data coverage). Same GROUP BY, different sort key.
SELECT
    indicator_name,
    COUNT(DISTINCT country_name) AS countries_reporting
FROM international_debt
GROUP BY indicator_name
ORDER BY countries_reporting DESC;


-- 6. Top 10 countries by total external debt stock (headline ranking).
SELECT
    country_name,
    ROUND(debt / 1e9, 2) AS total_external_debt_billions_usd
FROM international_debt
WHERE indicator_code = 'DT.DOD.DECT.CD'
ORDER BY debt DESC
LIMIT 10;


-- 7. Bottom 10 countries by total external debt stock (only countries that
--    actually report a value -- excludes missing data, not the same as zero).
SELECT
    country_name,
    ROUND(debt / 1e9, 3) AS total_external_debt_billions_usd
FROM international_debt
WHERE indicator_code = 'DT.DOD.DECT.CD'
ORDER BY debt ASC
LIMIT 10;


-- 8. Total external debt aggregated by region (JOIN + GROUP BY) -- compares
--    debt load across parts of the world rather than individual countries.
SELECT
    r.region,
    COUNT(*) AS countries,
    ROUND(SUM(d.debt) / 1e9, 1) AS total_debt_billions_usd,
    ROUND(AVG(d.debt) / 1e9, 2) AS avg_debt_per_country_billions_usd
FROM international_debt d
JOIN country_reference r ON d.country_code = r.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
GROUP BY r.region
ORDER BY total_debt_billions_usd DESC;


-- 9. Same, but grouped by World Bank income level -- do richer or poorer
--    countries carry more absolute external debt?
SELECT
    r.income_level,
    COUNT(*) AS countries,
    ROUND(SUM(d.debt) / 1e9, 1) AS total_debt_billions_usd
FROM international_debt d
JOIN country_reference r ON d.country_code = r.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
GROUP BY r.income_level
ORDER BY total_debt_billions_usd DESC;


-- 10. Debt relative to the size of the economy: top 10 by external debt as
--     % of GNI -- comparing values on a *normalized* basis, not raw USD.
--     (A small economy can carry a debt burden that dwarfs its own income.)
SELECT
    country_name,
    ROUND("DT.DOD.DECT.GN.ZS", 1) AS external_debt_pct_of_gni
FROM country_reference
WHERE "DT.DOD.DECT.GN.ZS" IS NOT NULL
ORDER BY "DT.DOD.DECT.GN.ZS" DESC
LIMIT 10;


-- 11. Debt-service burden: top 10 by total debt service as % of exports --
--     the share of a country's export earnings eaten up just by debt
--     repayments each year (a classic debt-distress early-warning metric).
SELECT
    country_name,
    ROUND("DT.TDS.DECT.EX.ZS", 1) AS debt_service_pct_of_exports
FROM country_reference
WHERE "DT.TDS.DECT.EX.ZS" IS NOT NULL
ORDER BY "DT.TDS.DECT.EX.ZS" DESC
LIMIT 10;


-- 12. Comparing debt to economic size directly: total external debt vs. GDP
--     per country, for the 20 biggest debtors (JOIN + derived ratio column).
SELECT
    d.country_name,
    ROUND(d.debt / 1e9, 1) AS total_debt_billions_usd,
    ROUND(r.gdp_current_usd / 1e9, 1) AS gdp_billions_usd,
    ROUND(100.0 * d.debt / NULLIF(r.gdp_current_usd, 0), 1) AS debt_pct_of_gdp
FROM international_debt d
JOIN country_reference r ON d.country_code = r.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
ORDER BY d.debt DESC
LIMIT 20;


-- 13. Composition check for the single most indebted country: how does its
--     debt break down across indicator types? (GROUP BY on a WHERE-filtered
--     single country -- useful drill-down pattern.)
SELECT
    indicator_name,
    ROUND(debt / 1e9, 2) AS debt_billions_usd
FROM international_debt
WHERE country_name = (
    SELECT country_name FROM international_debt
    WHERE indicator_code = 'DT.DOD.DECT.CD'
    ORDER BY debt DESC LIMIT 1
)
ORDER BY debt_billions_usd DESC;


-- 14. Average debt per country across every reported indicator (GROUP BY
--     country, AVG(debt)) -- the figure the dashboard's world map is colored
--     by. Different from query 6/7 (which use only the single "total stock"
--     indicator): this blends total stock, short-term, PPG, PNG, debt
--     service, etc. into one representative number per country.
SELECT
    country_name,
    ROUND(AVG(debt) / 1e9, 3) AS avg_debt_billions_usd,
    COUNT(*) AS indicators_averaged
FROM international_debt
GROUP BY country_name
ORDER BY avg_debt_billions_usd DESC
LIMIT 15;


-- 15. Year of peak historical external debt per country -- a self-join
--     pattern (a country's own maximum year, found via a correlated
--     subquery) rather than a plain GROUP BY. Restricted to the 10 largest
--     2024 debtors here; drop the WHERE country_name IN (...) filter to run
--     it for every country in debt_history.
SELECT
    h.country_name,
    h.year AS peak_year,
    ROUND(h.debt / 1e9, 1) AS peak_debt_billions_usd
FROM debt_history h
WHERE h.debt = (
    SELECT MAX(h2.debt) FROM debt_history h2 WHERE h2.country_code = h.country_code
)
AND h.country_name IN (
    'China', 'India', 'Brazil', 'Mexico', 'Turkiye', 'Indonesia',
    'Argentina', 'Colombia', 'Ukraine', 'Thailand'
)
ORDER BY peak_debt_billions_usd DESC;
