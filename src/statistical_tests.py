"""Formal hypothesis tests behind the GROUP BY comparisons in sql/analysis.sql.

Question: does external debt burden (debt as % of GDP) differ significantly
across World Bank income groups and regions, or could the differences the
GROUP BY tables show plausibly be noise?

Debt ratios are right-skewed (a few very high-debt countries), so normality
and equal-variance checks decide whether ANOVA or its nonparametric
counterpart (Kruskal-Wallis) is the right test; post-hoc pairwise
Mann-Whitney U tests (Bonferroni-corrected) identify which specific groups
differ.
"""
import itertools
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

MIN_GROUP_SIZE = 5


def groups_for(df, group_col, value_col):
    counts = df.groupby(group_col)[value_col].count()
    keep = counts[counts >= MIN_GROUP_SIZE].index
    sub = df[df[group_col].isin(keep)].dropna(subset=[value_col])
    return {name: g[value_col].values for name, g in sub.groupby(group_col)}, sub


def run_omnibus(groups, label):
    values = list(groups.values())
    normal_pvals = [stats.shapiro(v).pvalue for v in values if len(v) >= 3]
    all_normal = all(p > 0.05 for p in normal_pvals) if normal_pvals else False
    levene_p = stats.levene(*values).pvalue

    f_stat, anova_p = stats.f_oneway(*values)
    h_stat, kw_p = stats.kruskal(*values)

    print(f"\n=== {label} ===")
    print(f"Groups: {[(k, len(v)) for k, v in groups.items()]}")
    print(f"Shapiro normality per group (min p): "
          f"{min(normal_pvals):.4f}" if normal_pvals else "n/a", "-> ",
          "looks normal" if all_normal else "NOT all normal")
    print(f"Levene equal-variance p={levene_p:.4f} -> ",
          "equal variance" if levene_p > 0.05 else "unequal variance")
    print(f"One-way ANOVA: F={f_stat:.3f}, p={anova_p:.4f}")
    print(f"Kruskal-Wallis: H={h_stat:.3f}, p={kw_p:.4f}")

    return {
        "label": label,
        "group_sizes": {k: len(v) for k, v in groups.items()},
        "shapiro_all_normal": all_normal,
        "levene_p": round(levene_p, 4),
        "anova_f": round(float(f_stat), 4),
        "anova_p": round(float(anova_p), 4),
        "kruskal_h": round(float(h_stat), 4),
        "kruskal_p": round(float(kw_p), 4),
        "recommended_test": "ANOVA" if (all_normal and levene_p > 0.05) else "Kruskal-Wallis",
        "significant_at_0.05": bool(kw_p < 0.05),
    }


def pairwise_posthoc(groups):
    names = list(groups.keys())
    rows = []
    for a, b in itertools.combinations(names, 2):
        u, p = stats.mannwhitneyu(groups[a], groups[b], alternative="two-sided")
        rows.append({"group_a": a, "group_b": b, "u_stat": u, "p_raw": p})
    pdf = pd.DataFrame(rows)
    pdf["p_bonferroni"] = multipletests(pdf["p_raw"], method="bonferroni")[1]
    pdf["significant"] = pdf["p_bonferroni"] < 0.05
    return pdf.sort_values("p_bonferroni")


def boxplot(df, group_col, value_col, title, path):
    order = df.groupby(group_col)[value_col].median().sort_values(ascending=False).index
    data = [df[df[group_col] == g][value_col].dropna().values for g in order]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=order, vert=False, showmeans=True)
    ax.set_xlabel(value_col)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def main():
    df = pd.read_csv("data/country_features.csv")
    results = {}

    for group_col, label in [("income_level", "Debt/GDP by income level"),
                              ("region", "Debt/GDP by region")]:
        groups, sub = groups_for(df, group_col, "debt_pct_gdp")
        summary = run_omnibus(groups, label)

        posthoc = pairwise_posthoc(groups)
        print(posthoc.to_string(index=False))
        summary["posthoc_significant_pairs"] = (
            posthoc[posthoc["significant"]][["group_a", "group_b", "p_bonferroni"]]
            .round(4).to_dict(orient="records")
        )

        tukey = pairwise_tukeyhsd(sub["debt_pct_gdp"], sub[group_col])
        print(tukey.summary())

        results[group_col] = summary

        boxplot(sub, group_col, "debt_pct_gdp",
                f"External debt as % of GDP, by {group_col.replace('_', ' ')}",
                f"models/figures/boxplot_debt_pct_gdp_by_{group_col}.png")

    with open("models/statistical_tests.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nSaved models/statistical_tests.json and boxplot figures.")


if __name__ == "__main__":
    main()
