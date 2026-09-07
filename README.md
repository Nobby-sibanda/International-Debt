# 💰 International Debt

**Author:** Nobukhosi Sibanda
**Degree:** MSc Data Science (May 2026) | BSc Finance | Quantitative Analyst Student

A SQL-focused analysis of **World Bank International Debt Statistics (IDS)** — how much external debt
each country carries, who owes the most, who owes the least, and what's actually driving those numbers.
Built as a hands-on project for **grouping, totals, and comparing values in SQL**, backed by a live
SQLite database, a fully executed analysis notebook, and a captioned interactive dashboard.

All data is fetched live from the World Bank Open Data API at run time — no manual downloads. This
run covers **2024 figures for 120 countries** across 10 external-debt indicators.

---

## Data Source

| Source | What it provides | Coverage |
|--------|------------------|----------|
| **World Bank International Debt Statistics (IDS)** | External debt stocks & debt service, by instrument (total, short-term, public/publicly-guaranteed, private nonguaranteed, IBRD/IDA) | 2024, 120 reporting countries |
| **World Bank World Development Indicators** | GDP, GNI-relative debt ratios, export-relative debt-service ratios, population, reserves | 2024 |

Fetched via `src/fetch_data.py` from `api.worldbank.org/v2`. World Bank data is public domain (CC BY-4.0).
Several of the classic "AMT/DIS/INT" flow indicators (amortization, disbursement, interest by creditor
type) used in older versions of this dataset have since been archived on the public API — this project
uses the current, live-queryable set of stock (`DOD`) and debt-service (`TDS`) indicators instead; see
`data/indicator_glossary.json` for the full indicator name mapping.

---

## Project Structure

```
├── notebooks/
│   ├── International_Debt_Analysis.ipynb   # Main SQL analysis notebook (fully executed)
│   └── ML_Debt_Risk_Analysis.ipynb         # Classification, clustering, forecasting, stats, anomaly detection
├── src/
│   ├── fetch_data.py        # Pulls IDS + WDI data (2024 snapshot) from the World Bank API
│   ├── fetch_historical.py  # Pulls the full 1970-2024 external debt time series
│   ├── build_db.py          # Loads the CSVs into SQLite (3 tables)
│   ├── run_analysis.py      # Runs sql/analysis.sql end-to-end, saves each result set
│   ├── build_dashboard.py   # Generates the interactive HTML dashboard
│   ├── build_features.py    # Engineers the country x feature matrix used by all ML scripts below
│   ├── train_classifier.py  # Debt-distress risk classifier (logistic regression + gradient boosting)
│   ├── clustering.py        # K-means/hierarchical country debt-profile clustering + PCA
│   ├── forecast_debt.py     # ARIMA debt forecasts (top 10 debtors) with backtest
│   ├── statistical_tests.py # ANOVA/Kruskal-Wallis tests on debt/GDP by income level & region
│   └── anomaly_detection.py # Algorithmic YoY debt-spike detection (z-score + IsolationForest)
├── sql/
│   └── analysis.sql         # 15 documented queries: grouping, totals, comparisons, peak-year lookup
├── data/
│   ├── international_debt.csv        # Long-format country x indicator debt table (2024)
│   ├── country_reference.csv         # GDP, region, income level, ratios per country
│   ├── debt_time_series.csv          # Total external debt, every country, 1970-2024
│   ├── peak_debt_year.csv            # Each country's own historical peak year + debt level
│   ├── indicator_glossary.json       # indicator_code -> full World Bank name
│   ├── analysis_results/             # CSV output of every query in analysis.sql
│   ├── debt_distress_labels.csv      # IMF List-of-LIC-DSAs risk ratings (ground truth for the classifier)
│   ├── country_features.csv          # Engineered feature matrix, all 120 debt-reporting countries
│   ├── labeled_features.csv          # Feature matrix joined to IMF labels (63 countries)
│   ├── country_clusters.csv          # K-means/hierarchical cluster assignments + PCA coordinates
│   └── debt_anomalies.csv            # Per-country-year anomaly flags (z-score + IsolationForest)
├── models/
│   ├── classifier_*.pkl, classifier_metrics.json     # Trained classifiers + CV/test metrics
│   ├── clustering_metrics.json, forecast_metrics.json, statistical_tests.json, anomaly_detection.json
│   ├── figures/              # Saved PNGs: ROC curve, confusion matrices, PCA scatter, forecasts, boxplots
│   └── MODEL_CARD.md         # Methodology, results, and honest limitations for every ML addition
├── assets/
│   └── international_debt_dashboard.html   # Interactive Plotly dashboard (open in browser)
├── international_debt.db    # SQLite database (international_debt + country_reference + debt_history)
├── requirements.txt
└── README.md
```

## Quick Start

```bash
git clone https://github.com/Nobby-sibanda/International-Debt.git
cd International-Debt
pip install -r requirements.txt

# Re-fetch live data (optional -- international_debt.db is already committed)
python src/fetch_data.py
python src/fetch_historical.py
python src/build_db.py
python src/run_analysis.py

# Full notebook
jupyter notebook notebooks/International_Debt_Analysis.ipynb

# ML additions -- classification, clustering, forecasting, stats, anomaly detection
python src/build_features.py
python src/train_classifier.py
python src/clustering.py
python src/forecast_debt.py
python src/statistical_tests.py
python src/anomaly_detection.py
jupyter notebook notebooks/ML_Debt_Risk_Analysis.ipynb

# Interactive dashboard -- open directly in a browser, no Jupyter needed
open assets/international_debt_dashboard.html      # macOS
xdg-open assets/international_debt_dashboard.html  # Linux
```

---

## SQL Learning Focus

`sql/analysis.sql` is written as a self-contained set of 15 queries, in increasing order of complexity,
built specifically around three SQL skills:

1. **Grouping** — `GROUP BY` country, indicator, region, and income level to roll thousands of raw rows
   into meaningful summaries.
2. **Totals** — `SUM`, `AVG`, `COUNT` to turn a country x indicator table into headline numbers ("how
   much does the world owe in total?", "what's the average debt per indicator?", "what's each
   country's own average debt across all indicators?" — query 14, the figure behind the dashboard's
   world map).
3. **Comparing values** — `ORDER BY` + `LIMIT` for top-N/bottom-N rankings, `JOIN`s across the debt and
   reference tables, derived ratio columns (debt as % of GDP/GNI/exports) so raw dollar figures can be
   compared on a level playing field, and a correlated-subquery pattern (query 15) to find each
   country's own historical peak year from a third `debt_history` time-series table (1970–2024).

Runs on SQLite as shipped, and is portable to Postgres/MySQL with no changes beyond `ROUND()` semantics.

---

## Key Findings

| Metric | Result |
|--------|--------|
| Countries covered | **120** |
| Debt indicators tracked | **10** |
| Combined external debt (all countries) | **$8.94 trillion** |
| Largest single debtor | **China** — $2,419.8B (12.9% of its own GDP) |
| Average debt per country | **$75.7B** |
| Highest debt-to-GNI ratio | **Mozambique** — 350.6% of GNI |
| Highest debt-service burden | **El Salvador** — 96.2% of export earnings |
| Region carrying the most debt | **East Asia & Pacific** — $3.41T |
| Income group carrying the most debt | **Upper-middle income** — $6.73T |
| Only top-20 debtor with debt exceeding its own GDP | **Ukraine** — 101.4% of GDP (war financing) |

---

## Top 10 Most Indebted Countries (Absolute External Debt)

| # | Country | Total External Debt (2024) | Debt / GDP | Historical Peak |
|---|---------|---------------------:|-----------:|:-----------------|
| 1 | China | $2,419.8B | 12.9% | 2021 — $2,724.4B |
| 2 | India | $716.5B | 19.1% | 2024 (still climbing) |
| 3 | Brazil | $605.5B | 27.7% | 2023 — $607.4B |
| 4 | Mexico | $591.3B | 32.3% | 2019 — $617.5B |
| 5 | Türkiye | $515.0B | 37.9% | 2024 (still climbing) |
| 6 | Indonesia | $421.1B | 30.2% | 2024 (still climbing) |
| 7 | Argentina | $242.4B | 38.0% | 2019 — $280.7B |
| 8 | Colombia | $201.8B | 48.0% | 2024 (still climbing) |
| 9 | Ukraine | $193.5B | 101.4% | 2024 (still climbing) |
| 10 | Thailand | $191.8B | 36.2% | 2022 — $201.1B |

## Bottom 10 Least Indebted Countries (Absolute External Debt)

| # | Country | Total External Debt (2024) | Historical Peak |
|---|---------|---------------------:|:-----------------|
| 1 | Tonga | $0.173B | 2021 — $0.224B |
| 2 | Timor-Leste | $0.297B | 2023 — $0.306B |
| 3 | São Tomé and Príncipe | $0.326B | 2004 — $0.356B |
| 4 | Comoros | $0.386B | 2024 (still climbing) |
| 5 | Samoa | $0.395B | 2021 — $0.506B |
| 6 | Vanuatu | $0.520B | 2024 (still climbing) |
| 7 | Dominica | $0.570B | 2022 — $0.599B |
| 8 | Solomon Islands | $0.596B | 2024 (still climbing) |
| 9 | Eritrea | $0.693B | 2011 — $1.051B |
| 10 | St. Vincent and the Grenadines | $0.806B | 2024 (still climbing) |

*(Peak years computed from the full 1970-2024 World Bank external-debt time series in
`data/debt_time_series.csv` — see [Peak Historical Debt Year](#peak-historical-debt-year--what-was-happening)
below for what drove each peak.)*

> **Important caveat on the bottom 10:** ranking by raw USD debt mechanically rewards small population
> and GDP size, not sound debt management. Several of these countries — Dominica (~99.5% of GDP),
> St. Vincent and the Grenadines (113–116% of GDP), Eritrea (~211–219% of GDP, mostly domestic), and
> Comoros — are rated by the IMF/World Bank at **high risk of, or already in, debt distress**, despite
> having some of the smallest dollar-denominated debt stocks in the world. See the deep dive below.

---

## Peak Historical Debt Year — What Was Happening

The 2024 figures above are a single snapshot. Pulling the full 1970–2024 time series for each country
(`src/fetch_historical.py`) and finding each one's own maximum year shows something the snapshot
hides: **half of the top 10 are still climbing toward a new record in 2024, and half already peaked
years ago and have since paid down or restructured.** Same split shows up in the bottom 10.

### Top 10 — five still climbing, five past their peak

| Country | Peak year | Peak debt | What was happening |
|---------|:---------:|----------:|---------------------|
| **China** | 2021 | $2,724.4B | Peaked the same year the Evergrande property crisis broke — China's second-largest developer defaulted after Beijing's "three red lines" policy cut off refinancing, and Belt & Road overseas lending hit its riskiest point (128 emergency rescue loans worth $240B by end-2021). Debt has declined since as China pulled back from risky overseas lending and pushed property-sector deleveraging. |
| **India** | 2024 | $716.5B | Still climbing — no single peak event; a steady rise tracking GDP growth and capital-account liberalization, cushioned by large FX reserves. |
| **Brazil** | 2023 | $607.4B | Essentially flat into 2024. Coincides with Lula's January 2023 return to office and a new fiscal framework passed by Congress in August 2023 (shifting from a deficit target to a 1%-of-GDP surplus target by 2026) — external debt held roughly steady through the transition even as domestic debt kept rising. |
| **Mexico** | 2019 | $617.5B | Directly tied to Pemex's financial distress: S&P cut Pemex's credit profile in March 2019, Fitch downgraded it to junk in June 2019 (a day after downgrading Mexico's own sovereign rating), citing Pemex's ~$105B debt as a contingent liability worth 9% of GDP. Mexico injected $3.9B to stem the bleeding; debt has eased since as Pemex's balance sheet was de-risked. |
| **Türkiye** | 2024 | $515.0B | Still climbing — no single peak event yet, though 2025 data shows the debt/GDP ratio itself starting to decline (32.6%). |
| **Indonesia** | 2024 | $421.1B | Still climbing — driven by Prabowo-era infrastructure/commodity borrowing and a widening fiscal deficit. |
| **Argentina** | 2019 | $280.7B | Directly tied to the IMF's then-record $57B loan (2018, expanded through 2019) under President Macri, deployed to defend the peso during a currency crisis (peso fell ~50% in 2018). Only $44B was ever disbursed; successor Alberto Fernández refused the remainder. The IMF's own later review concluded the loan "did not deliver on its objectives." Debt fell after the 2020 restructuring. |
| **Colombia** | 2024 | $201.8B | Still climbing — the government suspended its own fiscal rule in mid-2025 after revenue shortfalls. |
| **Ukraine** | 2024 | $193.5B | Still climbing, mechanically — wartime financing needs since Russia's 2022 invasion, with no plateau yet. |
| **Thailand** | 2022 | $201.1B | Coincides with the tail of post-COVID recovery borrowing and the start of the Fed's global rate-hike cycle, which pressured the baht; the Bank of Thailand responded with rate hikes and extended debt-restructuring relief for borrowers through end-2023. Debt eased afterward as the hiking cycle passed. |

### Bottom 10 — mostly still climbing; the historical peaks are climate- or isolation-driven

| Country | Peak year | Peak debt | What was happening |
|---------|:---------:|----------:|---------------------|
| **Tonga** | 2021 | $0.224B | Twin shocks: COVID-19 border closures collapsed tourism and remittance-adjacent activity (GDP -2.5% FY2020, -3.5% FY2021), layered on 2020's Cyclone Harold. An IMF Rapid Credit Facility disbursement (Jan 2021) and World Bank pandemic-recovery financing (Nov 2021) landed on top of prior loan commitments — Tonga had actually stopped taking *new* external loans since 2018, so the 2021 peak is mostly earlier disbursements arriving during the COVID emergency, predating the January 2022 volcanic eruption/tsunami. |
| **Timor-Leste** | 2023 | $0.306B | Not a single incident — a steady, deliberate build-up of concessional infrastructure loans (roads, water/sanitation, an airport) from the Asian Development Bank (~65% of the total), World Bank, and JICA since 2012, with long average maturities (25.5 years). The near-plateau with 2024 reflects policy choice — Timor-Leste funds most spending from its oil Petroleum Fund, not debt — rather than any 2023 shock. |
| **São Tomé and Príncipe** | 2004 | $0.356B | Pre-HIPC-relief borrowing, including debt collateralized against anticipated Gulf of Guinea oil revenue after 2003 São Tomé–Nigeria Joint Development Zone oil-block auctions raised expectations of oil wealth that never materialized (production still hadn't arrived decades later). Debt fell sharply after the country reached its HIPC completion point in March 2007, when the World Bank/IMF cut it from ~$350M to ~$130M. |
| **Comoros** | 2024 | $0.386B | Still climbing — chronic remittance dependence and weak export diversification keep pushing debt up; rated high risk of debt distress by the IMF, but no single 2024 trigger event — a gradual trend rather than a shock. |
| **Samoa** | 2021 | $0.506B | COVID border closures devastated tourism (~20% of GDP), driving GDP contractions of -5% (2020) and -9.7% (2021). Compounded by the 2021 constitutional crisis — a disputed 25/25 election tie between the FAST party and the 22-year incumbent HRPP, unresolved from April to July 2021 — in which China's role as Samoa's largest creditor (over 40% of external debt) was a central campaign issue. Debt has eased significantly since as tourism recovered. |
| **Vanuatu** | 2024 | $0.520B | At its 2024 peak — the May 2024 Air Vanuatu bankruptcy forced a government-backed debt restructuring after the state absorbed the airline's obligations, compounding a December 2024 major earthquake on top of three cyclones already suffered in 2023. |
| **Dominica** | 2022 | $0.599B | Reflects sustained post-Hurricane Maria (2017) reconstruction borrowing — Maria destroyed ~90% of the housing stock and caused losses equal to 226% of GDP — compounded by a 16.6% GDP contraction in 2020 from COVID. The World Bank remains Dominica's largest creditor (36% of external public debt); 2022's 5.7% growth reflects tourism recovery layered on top of still-elevated reconstruction-era debt. |
| **Solomon Islands** | 2024 | $0.596B | Still climbing — driven by declining logging revenue (the traditional export base) and fiscal strain following the 2023 Pacific Games; the IMF is pushing diversification into fisheries and tourism, with no single 2024 shock beyond continued gradual borrowing. |
| **Eritrea** | 2011 | $1.051B | Coincides with UN Security Council Resolution 2023 (December 2011), which tightened sanctions over Eritrea's alleged support for al-Shabaab and its Djibouti border dispute, restricting diaspora-tax collection and flagging mining-sector transactions. The timing lines up with Eritrea's subsequent decades-long cutoff from concessional external finance — external debt has declined since 2011 even as *total* (mostly domestic) debt kept climbing. |
| **St. Vincent and the Grenadines** | 2024 | $0.806B | At its 2024 peak — Hurricane Beryl (July 2024), the strongest regional hurricane since 1875, destroyed over 90% of infrastructure in the Southern Grenadines, driving a sharp debt/GDP surge and a subsequent Moody's downgrade. |

---

## Country Deep Dive: Top 10 Most Indebted

Causes, current economic/political standing, and realistic debt-reduction levers for each — researched
from IMF Article IV consultations, World Bank country updates, and recent financial press (see
[References](#references)).

### 1. China — $2,419.8B (12.9% of GDP)
**Causes:** Decades of export-led industrialization financed with foreign capital, plus heavy
corporate and local-government borrowing (real estate, infrastructure) now layered on top of external
obligations. **Standing:** Growth is cooling (~4.9% in 2025, trending toward 4.4% in 2026);
manufacturing investment has flattened after years of expansion, though exports posted a record ~$1.2T
trade surplus in 2025. Domestic (non-financial-sector) debt, at 296% of GDP, dwarfs the external
figure. Politically centrally controlled and stable, but 2026 fiscal policy explicitly pairs strategic
industrial investment with austerity on local-government debt. **What could help:** rebalancing from
investment/export-led growth toward domestic consumption, capping local-government financing vehicles,
and further diversifying export markets.

### 2. India — $716.5B (19.1% of GDP)
**Causes:** External debt has climbed steadily — its fastest pace in seven years in FY25 — alongside
rapid GDP growth and capital-account liberalization, but remains manageable thanks to large FX
reserves and a mostly long-term maturity profile. **Standing:** The IT/business-services export sector
is the growth engine (~$90B revenue in 2025, forecast to $232B by 2033). Politically stable under a
dominant ruling party, though rated only "Partly Free" by Freedom House — a reputational rather than
fiscal risk. **What could help:** broadening exports beyond IT/services into manufacturing (via
production-linked incentive schemes), keeping reserve buffers ample, and managing rupee volatility to
avoid debt-servicing spikes.

### 3. Brazil — $605.5B (27.7% of GDP)
**Causes:** External debt itself is moderate; the real fiscal pressure is domestic — general government
debt is projected to rise from 87.3% of GDP (2024) toward 95% by 2026. **Standing:** The real has lost
value sharply in recent stretches, and agribusiness (a key export pillar) is seeing rising insolvencies
from high borrowing costs. Politically, President Lula's declining approval and legislative gridlock
have stalled pension/tax reform, with 2026 elections making near-term consolidation unlikely — some
analysts warn interest costs could exceed 60% of tax revenue. **What could help:** enforcing the
spending cap, passing stalled tax reform to broaden the base, and targeted credit support to reduce
the agribusiness sector's rate sensitivity.

### 4. Mexico — $591.3B (32.3% of GDP)
**Causes:** Debt has grown alongside Pemex's leveraged balance sheet (still $84.5B) and general
government debt crossing 60% of GDP in 2025 for the first time in over 20 years. **Standing:** The
nearshoring boom is the bright spot — the USMCA-compliant export share jumped from ~45% to 89% in
2025, backed by "Plan México," a large infrastructure and tax-incentive package through 2030.
Investment-grade rated (BBB/Baa2) but only two notches above speculative, with a negative outlook, and
debt service already exceeds health or education spending. **What could help:** continuing to de-risk
Pemex, capturing more nearshoring FDI in high-value manufacturing to grow the tax base, and maintaining
fiscal discipline to protect the credit rating.

### 5. Türkiye — $515.0B (37.9% of GDP)
**Causes:** Chronic current-account deficits, heavy reliance on external financing for growth, and a
long history of high inflation and lira depreciation have kept external debt structurally elevated.
**Standing:** Growth is moderate (~3.5% in 2025); disinflation is working but slowly, with inflation
still ~29–32% against a 37% policy rate. 2025 fiscal consolidation surprised positively, but rising
interest costs raise 2026 borrowing needs, and political tension keeps investor sentiment volatile.
**What could help:** sustaining the tight-monetary-policy disinflation path rather than cutting rates
prematurely, lengthening debt maturities to reduce rollover risk, and continuing to narrow the current
account deficit through export competitiveness.

### 6. Indonesia — $421.1B (30.2% of GDP)
**Causes:** Rapid infrastructure and commodity-linked borrowing under President Prabowo, with a
widening fiscal deficit (2.92% of GDP in 2025, near the legal 3% cap) financed partly externally.
**Standing:** Nickel, coal, and palm oil remain export pillars, with a strategic bet on a nickel-based
EV battery ecosystem — but the rupiah lost 14.3% of its value and markets saw roughly $37B in combined
capital outflows since Prabowo took office. Fiscal and monetary policy have reportedly been "out of
sync," and debt service is projected to exceed 47% of state revenue in 2026. **What could help:**
aligning fiscal and central-bank policy, broadening the tax base beyond commodity revenue, and slowing
deficit growth to defend currency stability.

### 7. Argentina — $242.4B (38.0% of GDP)
**Causes:** A long history of serial sovereign defaults, chronic inflation, and reliance on IMF
programs (18+ historical arrangements) to bridge external financing gaps. **Standing:** A sharp
turnaround under President Milei — the economy grew 4.4% in 2025 after a 1.7% contraction in 2024,
and inflation fell from over 200% to ~33% (though re-accelerating). S&P upgraded the sovereign rating
to 'B-' on improved external liquidity, and a new 4-year, $20B IMF Extended Fund Facility is regarded
as one of the Fund's more successful recent stabilization programs. **What could help:** staying the
course on fiscal discipline to keep IMF support flowing, continuing to build FX reserves against
~$20–25B/year in debt payments, and addressing the social cost of austerity to preserve the political
mandate for reform.

### 8. Colombia — $201.8B (48.0% of GDP)
**Causes:** A widening structural fiscal deficit — the government suspended its own fiscal rule in
mid-2025 after revenue shortfalls — has driven external debt up sharply, with private-sector debt
growing even faster (+9.3%) than public debt. **Standing:** President Petro's government has widened
social spending (subsidies, transfers) faster than revenue growth, and tension with the central bank
became public in March 2026, raising central-bank-independence concerns ahead of the 2026 election.
**What could help:** reinstating a credible, enforceable fiscal rule, broadening tax revenue rather
than expanding subsidy spending, and depoliticizing monetary policy to protect investor confidence.

### 9. Ukraine — $193.5B (101.4% of GDP)
**Causes:** Overwhelmingly driven by Russia's ongoing full-scale invasion since 2022 — military
spending absorbs roughly 60% of the total budget, leaving the government reliant on foreign and
official-sector support for pensions, wages, and humanitarian needs. A 2024 debt restructuring
delivered a 35.75% haircut. **Standing:** A new 48-month, $8.1B IMF Extended Fund Facility (approved
February 2026) sits inside a broader $136.5B 2026–29 external support package (EU facilities, G7 ERA
financing, bilateral aid); reconstruction needs are now estimated at $588B. **What could help:** this
is the one case on the list where debt reduction isn't primarily a domestic policy lever — the path
runs through continued concessional/grant financing, further restructuring, and ultimately a
settlement that lets reconstruction financing replace wartime deficit-covering.

### 10. Thailand — $191.8B (36.2% of GDP)
**Causes:** Financing tied to a manufacturing/export base plus tourism-dependent current-account
financing; external debt levels are considered moderate and well-covered by reserves. **Standing:**
Growth is decelerating (2.4% in 2025 toward ~1.6% forecast for 2026) as tourism recovery is uneven and
manufacturing faces global trade headwinds. A February 2026 snap election delivered a decisive win to
the conservative Bhumjaithai party under PM Anutin Charnvirakul — both the IMF and independent
commentators flag that sustained political stability, not just policy, is what the recovery now needs.
**What could help:** diversifying export markets and manufacturing beyond tourism-cyclical exposure,
using the newly stable government mandate to unlock delayed public investment, and building a
competitive position in the regional battery/EV supply chain.

---

## Country Deep Dive: Bottom 10 Least Indebted

The absolute-dollar ranking here mostly reflects **economy size and market access**, not fiscal
prudence — several of these nations carry a debt-to-GDP burden that rivals the biggest debtors above.

| Country | External Debt | The real story |
|---------|---------------:|-----------------|
| **Tonga** | $0.173B | Finances itself mainly via remittances (~49% of GDP) and grants, not loans. Debt/GDP has improved to 23.5%, but the IMF still rates it **high risk of debt distress** given exposure to cyclones and a narrow economic base. |
| **Timor-Leste** | $0.297B | Uniquely funds government spending by drawing down its Petroleum Fund (939% of non-oil GDP) instead of borrowing. Oil/gas production ceased in June 2025; the fiscal deficit is ~11% of GDP as it searches for non-oil growth before the Fund depletes. |
| **São Tomé and Príncipe** | $0.326B | Formally **in debt distress** due to unresolved legacy post-HIPC arrears, currently under a 52-month IMF Extended Credit Facility that constrains new borrowing. |
| **Comoros** | $0.386B | Remittance-dependent, high import dependence, weak export diversification; rated **high risk of debt distress**, compounded by weak governance and past political instability. |
| **Samoa** | $0.395B | Tourism and remittances (~20% of GDP) substitute for external borrowing. Risk was downgraded from high to **moderate** in 2024; key vulnerabilities are climate shocks and correspondent-banking pressure. |
| **Vanuatu** | $0.520B | Repeatedly hit by shocks — three cyclones in 2023, the Air Vanuatu bankruptcy (2024), and a major earthquake (Dec 2024). Debt-distress risk eased from high to **moderate** after Air Vanuatu's debt was restructured. |
| **Dominica** | $0.570B | The clearest case of low absolute debt hiding a severe relative burden: public debt is **~99.5% of GDP**, still rated high risk of debt distress, while funding a "Climate Resilient by 2030" plan. |
| **Solomon Islands** | $0.596B | Leans on declining logging revenue; the IMF is pushing diversification into fisheries and tourism amid fiscal strain and political-instability risk. |
| **Eritrea** | $0.693B | The starkest case: total debt (mostly *domestic*, ~211–219% of GDP) is masked by a tiny *external* figure — decades of political isolation, single-party rule, and past sanctions have cut it off from concessional external finance entirely. Formally in debt distress, pre-decision-point on HIPC relief. |
| **St. Vincent and the Grenadines** | $0.806B | Public debt surged to **113–116% of GDP** after the 2021 La Soufrière eruption and 2024's Hurricane Beryl (strongest regional hurricane since 1875). Moody's downgraded the country in July 2026. |

**Takeaway:** small island states in particular carry disproportionate climate-disaster exposure
relative to their fiscal buffers — a single hurricane or eruption can move their debt-to-GDP ratio by
double digits overnight, something an absolute-dollar ranking completely hides.

---

## Interactive Dashboard

`assets/international_debt_dashboard.html` is a self-contained page — KPI cards plus ten interactive
Plotly panels, each with a caption and source citation underneath, built from the same SQL queries as
the notebook:

1. **Top 10 Countries by Total External Debt** — headline ranking, absolute US$
2. **Bottom 10 Countries by Total External Debt** — smallest absolute debtors, with the size-vs-burden caveat
3. **World Map — Average External Debt per Country** — choropleth of each country's own average across all reported indicators
4. **Total External Debt by World Bank Region** — East Asia & Pacific and Latin America & Caribbean lead
5. **Total External Debt by Income Level** — upper-middle income carries the most in absolute terms
6. **Top 10 by External Debt as % of GNI** — size-adjusted debt burden (Mozambique highest, 350.6%)
7. **Top 10 by Debt Service as % of Exports** — annual repayment burden on export earnings (El Salvador highest)
8. **Debt vs. GDP — Top 20 Debtors** — log-log bubble chart; Ukraine stands out as the one economy whose debt exceeds its GDP
9. **Debt Composition — China (Largest Debtor)** — breakdown by instrument type; short-term debt is over half the total
10. **Top 10 Most-Indebted — Year of Peak Historical Debt** — which countries are still climbing to a new high in 2024 vs. already past their peak (see [Peak Historical Debt Year](#peak-historical-debt-year--what-was-happening) for the story behind each)

All charts support hover tooltips and are theme-aware (light/dark). Plotly is loaded from a CDN, so an
internet connection is needed the first time it's opened; the chart data itself is fully embedded and
works offline after that.

---

## Machine Learning Additions

The SQL layer above answers *what* the debt data shows. This section adds a modeling layer on the
same World Bank extract: a supervised classifier, unsupervised clustering, time-series forecasting
with a backtest, formal hypothesis tests, and algorithmic anomaly detection — each reported honestly,
including where the results are modest. Full methodology and every metric:
[`models/MODEL_CARD.md`](models/MODEL_CARD.md); full walkthrough with live-executed code:
[`notebooks/ML_Debt_Risk_Analysis.ipynb`](notebooks/ML_Debt_Risk_Analysis.ipynb); also surfaced as four
new panels in the [interactive dashboard](#interactive-dashboard).

| Addition | Method | Headline result |
|---|---|---|
| **Debt-distress risk classifier** | Logistic regression + gradient-boosted trees, 5-fold CV, on IMF [List of LIC DSAs](https://www.imf.org/external/Pubs/ft/dsa/DSAlist.pdf) labels (63 PRGT-eligible countries) | AUC ~0.55-0.61 — honestly modest; static balance-sheet ratios only partially explain the IMF's own forward-looking rating |
| **Country debt-profile clustering** | K-means (k chosen by silhouette) + PCA, all 120 countries, no labels used | 2 clusters: concessional/public-debt-heavy vs. market-financed/private-debt-heavier |
| **Debt forecasting (top 10 debtors)** | Per-country ARIMA on log(debt), AIC-selected order, 5-year backtest, 2025-2027 forecast | 14.2% average backtest MAPE; largest errors (China, Argentina) line up with known structural breaks |
| **Statistical testing** | Kruskal-Wallis / ANOVA + Bonferroni-corrected post-hoc, on debt/GDP by income level & region | No significant difference by income level (p=0.38) or region (p=0.44) — absolute-dollar gaps are an economy-size effect, not a burden effect |
| **Anomaly detection** | Robust z-score (median/MAD) on YoY debt change, cross-checked with IsolationForest | Confirms "peak level" and "YoY shock" are different signals; recovers Argentina's 2018 IMF-crisis jump when scanning 2000+ |

**On the classifier's modest AUC:** this is reported as a genuine finding, not hidden or tuned away.
The IMF's own debt-distress rating incorporates forward debt-service projections, growth/export
assumptions, arrears status, and program conditionality — none of which exist in a point-in-time
balance-sheet snapshot. That static ratios only partially predict the IMF's own classification is
itself a defensible, useful result.

---

## Methodology Notes

- **Year:** all figures are for **2024**, the most recent year with broad cross-country coverage on the
  live World Bank API at the time this was run (`DT.DOD.DECT.CD` returns data for 129 economies at
  `mrv=1`, all dated 2024).
- **Indicator set:** several of the classic debt-flow indicators (`DT.AMT.*` amortization,
  `DT.DIS.*` disbursements, `DT.INT.*` interest by creditor type) used in older versions of this kind
  of dataset currently return "indicator not found" via the public API — they appear to have been
  archived from live querying even though their metadata still exists. This project uses the
  currently-live stock (`DT.DOD.*`) and debt-service (`DT.TDS.*`) indicators instead, confirmed working
  by direct API testing before the fetch script was finalized.
- **Aggregates excluded:** World Bank region/income-group rows (e.g. "East Asia & Pacific excluding
  high income," "Low & middle income") are filtered out of `international_debt` and
  `country_reference` — only actual countries are included; regional/income totals in this README and
  the dashboard are computed via `GROUP BY` on the real country-level rows, not taken from the Bank's
  own pre-aggregated rows.
- **Bottom-10 framing:** absolute-dollar debt rankings mechanically favor small economies. This README
  and the dashboard both pair the raw ranking with debt-to-GDP/GNI context specifically so that isn't
  misread as "these countries manage debt well."

---

## References

**Data**
- [World Bank Open Data API — International Debt Statistics](https://api.worldbank.org/v2/) (source ID 6)
- [World Bank IDS program page](https://www.worldbank.org/en/programs/debt-statistics)

**Top 10 peak-year events**
- [Congress.gov — Evergrande Group and China's Debt Challenges](https://www.congress.gov/crs-product/IF11953)
- [AidData — Belt and Road bailout lending reaches record levels](https://www.aiddata.org/blog/belt-and-road-bailout-lending-reaches-record-levels)
- [CNN Business — China spent $240 billion bailing out indebted countries](https://www.cnn.com/2023/03/28/economy/china-rescue-lending-belt-and-road-study-intl-hnk/index.html)
- [Euronews — S&P downgrades debt-laden Pemex](https://www.euronews.com/2019/03/04/sp-downgrades-debt-laden-mexican-state-oil-firm-pemex)
- [Investing.com — Fitch downgrades Pemex debt to 'junk'](https://investing.com/news/commodities-news/fitch-downgrades-pemex-debt-to-junk-in-fresh-blow-to-mexico-1891081)
- [AOL/Reuters — Mexico to inject $3.9 billion in Pemex](https://www.aol.com/mexico-inject-3-9-billion-pemex-seeks-prevent-014104506--business.html)
- [Atlantic Council — IMF throws Argentina a $57 billion lifeline](https://www.atlanticcouncil.org/blogs/new-atlanticist/imf-throws-argentina-a-57-billion-lifeline/)
- [Buenos Aires Times — IMF report concludes 2018 loan "did not deliver on its objectives"](https://www.batimes.com.ar/news/economy/imf-report-concludes-2018-loan-to-argentina-did-not-deliver-on-its-objectives.phtml)
- [Global Policy Watch — Brazil's Lula Administration Presents New Fiscal Framework](https://www.globalpolicywatch.com/2023/04/brazils-lula-administration-presents-new-fiscal-framework/)
- [Statista — Brazil government external debt](https://statista.com/statistics/1057102/brazil-government-external-debt-share-gdp)
- [Macrotrends — Thailand External Debt 1970–2025](https://macrotrends.net/global-metrics/countries/tha/thailand/external-debt-stock)
- [AMRO — Thailand's Recovery is Firming but Risks Remain](https://amro-asia.org/thailands-recovery-is-firming-but-risks-and-structural-challenges-remain/)

**Top 10 deep dive**
- [Congress.gov CRS — China's Economy: Current Trends and Issues](https://www.congress.gov/crs-product/IF11667)
- [Rhodium Group — China's Economy: Rightsizing 2025, Looking Ahead to 2026](https://rhg.com/research/chinas-economy-rightsizing-2025-looking-ahead-to-2026/)
- [World Bank — China Economic Update, December 2025](https://thedocs.worldbank.org/en/doc/600cd53e2bb24d516b8c3489e5d2c187-0070012025/original/CEU-December-2025-EN.pdf)
- [Business Standard — India's external debt rises to $762.8bn](https://www.business-standard.com/finance/news/india-s-external-debt-rises-to-762-8-bn-at-end-march-2026-rbi-data-126062900940_1.html)
- [Grand View Research — India IT Services Market Outlook 2026–2033](https://www.grandviewresearch.com/horizon/outlook/it-services-market/india)
- [Freedom House — India: Country Profile](https://freedomhouse.org/country/india)
- [AEI — Brazil's Slow-Burning Economic Crisis](https://www.aei.org/op-eds/brazils-slow-burning-economic-crisis-might-be-the-u-s-future/)
- [Deloitte — Brazil Economic Outlook, February 2026](https://www.deloitte.com/us/en/insights/topics/economy/americas/brazil-economic-outlook.html)
- [Rio Times — Mexico Economy 2026: Nearshoring, Banxico, Peso](https://www.riotimesonline.com/mexico-economy-2026-outlook/)
- [Mexico Business News — Mexico Hits Record Public Debt Level](https://mexicobusiness.news/finance/news/mexico-hits-record-public-debt-level-ministry-finance)
- [S&P Global — Mexico's New Administration Faces Old Challenges](https://spglobal.com/ratings/en/research/articles/240603-mexico-s-new-administration-faces-old-challenges-13134599)
- [Take-profit.org — Turkey External & Government Debt to GDP](https://take-profit.org/en/statistics/government-debt-to-gdp/turkey/)
- [World Bank — Turkey Overview](https://www.worldbank.org/en/country/turkey/overview)
- [Fulcrum — Prabowo's Fiscal Reckoning and Governance Implications](https://fulcrum.sg/squeezed-from-both-sides-prabowos-fiscal-reckoning-and-governance-implications/)
- [Asia Times — Indonesia's debt wall hits an economy running on borrowed time](https://asiatimes.com/2026/05/indonesias-debt-wall-hits-an-economy-running-on-borrowed-time/)
- [Bloomberg — Indonesia's Prabowo Pushes Deficit to Edge of Post-Crisis Limit](https://www.bloomberg.com/news/articles/2026-01-08/indonesia-fiscal-deficit-soars-to-2-92-of-gdp-near-legal-limit)
- [Rio Times — Argentina Economy 2026: Milei Cuts Inflation to 33%](https://www.riotimesonline.com/argentina-economy-2026-guide/)
- [Al Jazeera — IMF unlocks $4.7bn for Argentina amid Milei austerity](https://www.aljazeera.com/news/2024/1/11/imf-unlocks-4-7bn-for-argentina-amid-economic-crisis-milei-austerity-cuts)
- [PIIE — Argentina's fragile monetary framework](https://www.piie.com/blogs/realtime-economics/2026/argentinas-fragile-monetary-framework-risks-renewed-volatility)
- [ColombiaOne — Colombia's External Debt Surges by US$30 Billion to 55% of GDP](https://colombiaone.com/2026/05/13/colombia-external-debt-surges-55-of-gdp/)
- [CEPR — Colombia under Petro: Social Gains Amid Monetary and Fiscal Constraints](https://cepr.net/publications/colombia-under-petro-social-gains-amid-monetary-and-fiscal-constraints/)
- [IMF — Ukraine: First Review of Extended Fund Facility Arrangement (2026)](https://www.imf.org/en/news/articles/2026/07/20/pr26254-ukraine-imf-completes-1st-review-of-eff-arrangement-concludes-2026-aiv-consultation)
- [Scope Ratings — Ukrainian debt sustainability challenges](https://www.scoperatings.com/ratings-and-research/research/EN/179352)
- [Nation Thailand — Thailand's economy forecasted to grow 2% in 2026](https://www.nationthailand.com/business/economy/40062492)
- [IMF — Thailand: 2025 Article IV Consultation](https://www.imf.org/en/news/articles/2026/02/13/pr26048-thailand-imf-executive-board-concludes-2025-article-iv-consultation-with-thailand)
- [Thai Examiner — Thailand needs political stability and more foreign tourists](https://www.thaiexaminer.com/thai-news-foreigners/2026/02/18/the-battle-for-2026s-economy-has-begun-thailand-needs-political-stability-and-more-foreign-tourists/)

**Bottom 10 deep dive**
- [IMF — Tonga 2024 Article IV Consultation](https://www.elibrary.imf.org/view/journals/002/2024/326/article-A001-en.xml)
- [Matangi Tonga — Tongan economy outlook, November 2025](https://matangitonga.to/2025/11/13/tongan-economy-outlook-favourable-significant-risks-reports-imf)
- [IMF — Timor-Leste 2025 Article IV Consultation](https://www.imf.org/en/publications/cr/issues/2025/09/25/democratic-republic-of-timor-leste-2025-article-iv-consultation-press-release-staff-report-570720)
- [East Asia Forum — Timor-Leste's search for growth beyond oil](https://eastasiaforum.org/2026/02/26/timor-lestes-search-for-growth-beyond-oil/)
- [IMF — São Tomé and Príncipe 2025 Article IV / ECF Review](https://www.elibrary.imf.org/view/journals/002/2025/228/article-A001-en.xml)
- [IMF — São Tomé and Príncipe ECF Third Review, April 2026](https://www.imf.org/en/news/articles/2026/04/09/pr26109-sao-tome-and-principe-imf-completes-mission-third-review-ecf-arrangement)
- [IMF Country Report 26/47 — Comoros](https://www.imf.org/-/media/files/publications/cr/2026/english/1comea2026001-source-pdf.pdf)
- [African Development Bank — Comoros Economic Outlook](https://www.afdb.org/en/countries/east-africa/comoros/comoros-economic-outlook)
- [IMF Country Report 25/32 — Samoa](https://www.imf.org/-/media/Files/Publications/CR/2025/English/1wsmea2025001-print-pdf.ashx)
- [Asian Development Bank — Vanuatu, April 2026](https://www.adb.org/sites/default/files/publication/1135881/van-ado-april-2026.pdf)
- [IMF — Vanuatu: Return to Sustainable Growth After Airline Bankruptcy](https://www.imf.org/en/news/articles/2024/11/25/cf-how-vanuatu-can-return-to-sustainable-growth-after-airline-bankruptcy)
- [IMF — Dominica Staff Concluding Statement, 2026 Article IV Mission](https://www.imf.org/en/news/articles/2026/03/27/mcs-03272026-dominica-staff-concluding-statement-of-the-2026-article-iv-mission)
- [IMF — Dominica 2025 Article IV Consultation](https://www.imf.org/en/News/Articles/2025/06/11/pr-25193-dominica-imf-concludes-2025-art-iv-consultation)
- [IMF — Solomon Islands 2026 Article IV Consultation](https://www.imf.org/en/news/articles/2026/07/07/pr26237-solomon-islands-imf-executive-board-concludes-2026-article-iv-consultation)
- [Pacific Islands Business Council — Solomon Islands growth steady, IMF urges reforms](https://apibc.org.au/2026/solomon-islands-growth-steady-at-3-5-as-imf-urges-reforms/)
- [Birr Metrics — IMF Skips Eritrea Again in World Economic Outlook Over Data Void](https://birrmetrics.com/imf-skips-eritrea-again-in-world-economic-outlook-over-data-void/)
- [Awate.com — The Debt-Free Illusion: Rethinking Eritrea's Economic Self-Reliance](https://awate.com/the-debt-free-illusion-rethinking-eritreas-economic-self-reliance/)
- [BTI 2026 — Eritrea Country Report](https://bti-project.org/en/reports/country-report/ERI)
- [IMF — St. Vincent and the Grenadines 2026 Article IV Consultation](https://www.imf.org/en/news/articles/2026/06/12/pr-26205-st-vincent-and-the-grenadines-imf-concludes-2026-art-iv-consult)
- [iWitness News — Moody's downgrade, Vincentians' burden, July 2026](https://www.iwnsvg.com/2026/07/19/moodys-downgrade-vincentians-burden/)
- [World Bank — Hurricane Beryl support for St. Vincent and the Grenadines](https://www.worldbank.org/en/news/press-release/2024/10/18/world-bank-to-support-hurricane-beryl-affected-communities-in-st-vincent-and-the-grenadines)

**Bottom 10 peak-year events**
- [World Bank — Tonga Second Resilience Development Policy Financing](https://documents1.worldbank.org/curated/en/529241654609629236/pdf/Tonga-Second-Resilience-Development-Policy-Financing-Supplemental-Financing.pdf)
- [IMF Country Report 21/26 — Tonga](https://www.imf.org/-/media/files/publications/cr/2021/english/1tonea2021001.pdf)
- [IMF — Tonga: Executive Board Approves RCF Disbursement, January 2021](https://www.imf.org/en/news/articles/2021/01/26/pr2122-tonga-imf-executive-board-approves-disbursement-to-tonga)
- [World Bank — Support for Post-Pandemic Recovery in Tonga, November 2021](https://www.worldbank.org/en/news/press-release/2021/11/24/support-for-post-pandemic-recovery-resilience-and-jobs-in-tonga)
- [IMF/World Bank — Timor-Leste Joint Debt Sustainability Analysis](https://documents1.worldbank.org/curated/en/966741626972945143/pdf/Timor-Leste-Joint-World-Bank-IMF-Debt-Sustainability-Analysis.pdf)
- [Macrotrends — Timor-Leste External Debt, 2012–2025](https://macrotrends.net/global-metrics/countries/tls/timor-leste/external-debt-stock)
- [African Development Bank — Debt Vulnerabilities in São Tomé and Príncipe](https://www.afdb.org/sites/default/files/documents/publications/aeb_volume_11_issue_2_debt_vulnerabilities_in_sao_tome_and_principe_.pdf)
- [World Bank — São Tomé and Príncipe HIPC Debt Relief](https://documents.worldbank.org/en/publication/documents-reports/documentdetail/602321583529078584/sao-tome-and-principe-enhanced-heavily-indebted-poor-countries-hipc-debt-initiative)
- [World Socialist Web Site — 2021 Samoan constitutional crisis](https://www.wsws.org/en/articles/2021/05/28/samo-m28.html)
- [East Asia Forum — Samoa's political crisis reveals cracks in the Pacific](https://eastasiaforum.org/2021/06/09/samoas-political-crisis-reveals-cracks-in-the-pacific/)
- [World Bank — Dominica country financing/creditor documents](https://documents1.worldbank.org/curated/en/099080525182022651/pdf/BOSIB-f00e50aa-1e38-4af2-a188-30413815e431.pdf)
- [GFDRR — Dominica Hurricane Maria Post-Disaster Assessment](https://www.gfdrr.org/en/dominica-hurricane-maria-post-disaster-assessment-and-support-recovery-planning)
- [UN News — Security Council expands sanctions on Eritrea, December 2011](https://news.un.org/en/story/2011/12/397282)
- [UN Press — Security Council Resolution 2023 (2011) text](https://press.un.org/en/2011/sc10471.doc.htm)

---

## License

MIT
