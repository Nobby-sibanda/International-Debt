# Model Card — International Debt ML Additions

Companion models to the SQL analysis, built on the same World Bank IDS/WDI
extract. All training scripts live in `src/`, all artifacts in this folder,
full walkthrough in `notebooks/ML_Debt_Risk_Analysis.ipynb`.

---

## 1. Debt-distress risk classifier

**Task:** predict whether a country is at High/In-debt-distress risk (vs.
Low/Moderate) per the IMF's own List of LIC DSAs, from static balance-sheet
ratios.

**Data:** `data/labeled_features.csv` — 63 countries (of the 120 in this
project's debt dataset) that appear on the IMF's [List of LIC DSAs for
PRGT-Eligible Countries](https://www.imf.org/external/Pubs/ft/dsa/DSAlist.pdf)
(as of March 31, 2026). 29 high-risk / 34 low-moderate-risk — reasonably
balanced. **This label only exists for low-income/PRGT-eligible countries** —
it cannot be produced for the top-10 debtors (China, India, Brazil, etc.),
which is why this model and the README's qualitative deep dive answer
different questions.

**Features:** debt/GNI, debt/GDP, debt-service/exports, debt-service/total
debt, reserves/debt, short-term/PPG/private-nonguaranteed/multilateral debt
composition shares, debt per capita, GDP per capita, income level (one-hot).
`region` was tested as a feature too but dropped — 6 levels against n=63
added cross-validation noise rather than signal (see training log).

**Models:** logistic regression (C=0.3, standardized features) and gradient-
boosted trees (`n_estimators=50, max_depth=2`) — kept shallow given the
small sample. Evaluated with 5-fold stratified cross-validation (primary
metric, since a single 63-row holdout is noisy) plus a 25% held-out test
split for a confusion matrix / ROC curve snapshot.

**Results:**

| Model | 5-fold CV ROC-AUC | Held-out test ROC-AUC |
|---|---|---|
| Logistic regression | 0.61 ± 0.14 | 0.57 |
| Gradient boosting | 0.53 ± 0.22 | 0.64 |

Full numbers, confusion matrices, and feature importances: `classifier_metrics.json`,
`figures/roc_curve.png`, `figures/confusion_matrices.png`, `figures/feature_importance.png`.

**Honest limitation — read before citing this model:** AUC ~0.55-0.61 is
modest, and it's a genuine finding, not a bug. It was stable across every
feature-set/regularization variant tried (see training log in the notebook).
The IMF's own DSA rating is not a function of a balance-sheet snapshot — it
bakes in forward debt-service projections, growth/export assumptions, arrears
status, and program conditionality that this dataset doesn't have. The
takeaway is that static point-in-time ratios only partially explain the
IMF's own risk classification — which is itself a useful, defensible result
for a portfolio project, and is reported here rather than hidden or
massaged into a better-looking number.

---

## 2. Country debt-profile clustering

**Task:** find natural groupings of countries by debt profile, unsupervised
(no distress labels used).

**Data/features:** same 11 numeric ratios as the classifier, all 120 debt-
reporting countries (`data/country_features.csv`).

**Method:** K-means, k chosen by max silhouette score over k=2..7 (chosen
k=2, silhouette=0.22 — see `figures/cluster_k_selection.png`); agglomerative
clustering fit alongside for comparison (89.2% label agreement with k-means).
2D PCA projection for visualization (`figures/pca_clusters.png`).

**Result:** the two clusters read as "concessional / public-debt-heavy, lower
income" (median debt/GDP 38%, 72% public-PPG debt, 16% multilateral) vs.
"market-financed / private-debt-heavier, higher income" (median debt/GDP
58%, 48% public-PPG, 33% private-nonguaranteed). Silhouette scores across
all k (0.13–0.22) are modest — debt profiles form more of a continuum than
sharply separated groups, which is reported honestly rather than forcing a
larger, prettier-looking k. Full profile table: `clustering_metrics.json`.

---

## 3. Time-series forecasting (top 10 debtors)

**Task:** forecast 2025–2027 external debt for the 10 largest 2024 debtors.

**Method:** per-country ARIMA on log(debt), order chosen by AIC grid search
(p,d,q ∈ 0..2). Backtested by holding out the actual 2020–2024 values,
refit on the full 1970–2024 series for the real forecast, 95% CI reported.

**Backtest accuracy (MAPE against actual 2020-2024):** average 14.2% across
the 10 countries; range 2.1% (Türkiye) to 32.2% (Argentina). The two worst
performers — China (23.9%) and Argentina (32.2%) — are exactly the two
countries whose README deep-dive documents a sharp structural break
(Evergrande-era deleveraging; 2020 sovereign restructuring after the IMF
program) that a linear ARIMA can't anticipate. That the model's largest
errors line up with the known shock years is a sanity check, not a
coincidence. Full numbers: `forecast_metrics.json`, chart: `figures/forecast_top10.png`.

---

## 4. Statistical testing

**Question:** do debt/GDP burdens actually differ significantly across
income groups or regions, or do the GROUP BY tables in `sql/analysis.sql`
just show noise?

**Method:** Shapiro-Wilk + Levene tests to check ANOVA assumptions (debt
ratios are right-skewed → assumptions fail), so Kruskal-Wallis is the
primary test, with pairwise Mann-Whitney U (Bonferroni-corrected) as
post-hoc, and ANOVA/Tukey HSD reported alongside for comparison.

**Result:** no significant difference in debt/GDP by income level
(Kruskal-Wallis p=0.38) or by region (p=0.44). This is a genuinely useful
finding: the large *absolute*-dollar differences by region/income that the
SQL queries surface are a function of economy size, not evidence that any
income group or region is systematically more debt-burdened *relative to
its own GDP* — directly reinforcing the "bottom-10 caveat" already in the
README. Full output: `statistical_tests.json`.

---

## 5. Anomaly detection on the debt time series

**Task:** algorithmically flag anomalous year-over-year debt moves, instead
of relying only on manual research for the "peak year" narrative.

**Method:** per-country robust z-score (median/MAD, threshold |z|>2.5) on
YoY %% change, cross-checked against a pooled IsolationForest over
(level, YoY change, rolling volatility).

**Result:** 0/10 top debtors have an auto-flagged anomaly within a year of
their README-researched peak year — and that mismatch is itself the
finding, not a failure. "Peak year" is the single highest debt *level*;
"anomaly" is an unusually large *YoY move*. Five of the top 10 (India,
Türkiye, Indonesia, Colombia, Ukraine) are "still climbing" per the
README — a steady upward trend has no outlier move at its current maximum,
so no anomaly is expected there by construction. Restricting the anomaly
scan to 2000+ (closer in scale to today's debt levels) does surface
Argentina's 2018 IMF-program jump, consistent with the README narrative.
Full output: `anomaly_detection.json`, chart: `figures/anomaly_flags_top10.png`.

---

## Reproducing

```bash
python src/build_features.py       # -> data/country_features.csv, data/labeled_features.csv
python src/train_classifier.py     # -> models/classifier_*.pkl, classifier_metrics.json
python src/clustering.py           # -> data/country_clusters.csv, clustering_metrics.json
python src/forecast_debt.py        # -> models/forecast_metrics.json
python src/statistical_tests.py    # -> models/statistical_tests.json
python src/anomaly_detection.py    # -> data/debt_anomalies.csv, anomaly_detection.json
```

All random states are fixed (`random_state=42`) for reproducibility.
