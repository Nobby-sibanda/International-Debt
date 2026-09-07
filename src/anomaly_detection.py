"""Algorithmically flag anomalous year-over-year debt moves, instead of only
relying on the manually researched "peak year" already in the README.

Two independent detectors, cross-checked against each other:
  1. Per-country robust z-score (median/MAD) on YoY %% change -- interpretable,
     tuned to each country's own volatility.
  2. IsolationForest over pooled (level, YoY change, rolling volatility)
     features across all country-years -- a global, model-based check.

Output for the top 10 debtors is compared against the manually curated
peak-year narrative in the README as a sanity check on both methods.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

TOP_10 = ["China", "India", "Brazil", "Mexico", "Turkiye", "Indonesia",
          "Argentina", "Colombia", "Ukraine", "Thailand"]
Z_THRESHOLD = 2.5
KNOWN_PEAK_YEARS = {  # from README's manually researched deep dive
    "China": 2021, "India": 2024, "Brazil": 2023, "Mexico": 2019,
    "Turkiye": 2024, "Indonesia": 2024, "Argentina": 2019, "Colombia": 2024,
    "Ukraine": 2024, "Thailand": 2022,
}


def robust_zscore_flags(hist):
    hist = hist.sort_values(["country_code", "year"]).copy()
    hist["yoy_pct"] = hist.groupby("country_code")["debt"].pct_change()

    def zscore(group):
        med = group.median()
        mad = (group - med).abs().median() * 1.4826  # MAD -> std-equivalent
        if mad == 0 or np.isnan(mad):
            return pd.Series(0.0, index=group.index)
        return (group - med) / mad

    hist["z_score"] = hist.groupby("country_code")["yoy_pct"].transform(zscore)
    hist["flag_zscore"] = hist["z_score"].abs() > Z_THRESHOLD
    return hist


def isolation_forest_flags(hist):
    hist = hist.sort_values(["country_code", "year"]).copy()
    hist["yoy_pct"] = hist.groupby("country_code")["debt"].pct_change()
    hist["rolling_vol"] = (hist.groupby("country_code")["yoy_pct"]
                            .transform(lambda s: s.rolling(5, min_periods=3).std()))
    feats = hist[["debt", "yoy_pct", "rolling_vol"]].fillna(0)
    iso = IsolationForest(contamination=0.03, random_state=42, n_estimators=200)
    hist["flag_isoforest"] = iso.fit_predict(feats) == -1
    return hist


def main():
    hist = pd.read_csv("data/debt_time_series.csv")
    hist = robust_zscore_flags(hist)
    hist = isolation_forest_flags(hist)
    hist["flag_both"] = hist["flag_zscore"] & hist["flag_isoforest"]

    hist.to_csv("data/debt_anomalies.csv", index=False)

    summary = {}
    fig, axes = plt.subplots(2, 5, figsize=(22, 8))
    for ax, country in zip(axes.flat, TOP_10):
        sub = hist[hist["country_name"] == country].sort_values("year")
        flagged = sub[sub["flag_zscore"]]
        known_peak = KNOWN_PEAK_YEARS[country]

        near_known = bool(((flagged["year"] - known_peak).abs() <= 1).any())
        summary[country] = {
            "readme_peak_year": known_peak,
            "auto_flagged_years_zscore": flagged["year"].tolist(),
            "auto_flagged_years_isoforest": sub[sub["flag_isoforest"]]["year"].tolist(),
            "flagged_within_1yr_of_readme_peak": near_known,
        }

        ax.plot(sub["year"], sub["debt"] / 1e9, color="black", linewidth=1)
        ax.scatter(flagged["year"], flagged["debt"] / 1e9, color="red", zorder=5,
                    label="z-score flag", s=30)
        ax.axvline(known_peak, color="gray", linestyle="--", alpha=0.5)
        ax.set_title(country, fontsize=10)
        ax.set_ylabel("US$ billions")
        ax.tick_params(labelsize=8)

    axes.flat[0].legend(fontsize=7)
    fig.suptitle("Auto-flagged debt anomalies (red) vs. manually researched "
                 "peak year (dashed line) -- top 10 debtors")
    fig.tight_layout()
    fig.savefig("models/figures/anomaly_flags_top10.png", dpi=150)

    n_match = sum(v["flagged_within_1yr_of_readme_peak"] for v in summary.values())
    print(f"Anomaly detector flagged a year within +/-1 of the researched peak "
          f"for {n_match}/10 top debtors")
    for country, v in summary.items():
        print(f"  {country}: README peak={v['readme_peak_year']}, "
              f"z-score flags={v['auto_flagged_years_zscore']}, "
              f"match={v['flagged_within_1yr_of_readme_peak']}")

    total_flags = int(hist["flag_zscore"].sum())
    both_flags = int(hist["flag_both"].sum())
    print(f"\nTotal z-score anomaly years (all 121 countries): {total_flags}")
    print(f"Agreed by both z-score and IsolationForest: {both_flags}")

    with open("models/anomaly_detection.json", "w") as f:
        json.dump({
            "z_threshold": Z_THRESHOLD,
            "top10_vs_readme": summary,
            "total_flagged_country_years_zscore": total_flags,
            "total_flagged_country_years_both_methods": both_flags,
        }, f, indent=2)

    print("\nSaved data/debt_anomalies.csv, models/anomaly_detection.json, "
          "models/figures/anomaly_flags_top10.png")


if __name__ == "__main__":
    main()
