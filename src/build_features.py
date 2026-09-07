"""Build a country x feature matrix from the raw World Bank extracts.

Pivots the long-format `international_debt` table to one row per country,
joins the GDP/region/income reference table, engineers debt-composition and
debt-burden ratios, and (separately) attaches IMF LIC-DSA debt-distress
labels for the subset of countries that have one.

Outputs
-------
data/country_features.csv   -- all 120 debt-reporting countries, unlabeled
data/labeled_features.csv   -- the subset with an IMF risk_rating label
"""
import pandas as pd

INDICATOR_COLUMNS = {
    "DT.DOD.DECT.CD": "total_debt_usd",
    "DT.DOD.DPPG.CD": "public_ppg_debt_usd",
    "DT.DOD.DSTC.CD": "short_term_debt_usd",
    "DT.DOD.DPNG.CD": "private_png_debt_usd",
    "DT.DOD.MWBG.CD": "world_bank_debt_usd",
    "DT.DOD.MIBR.CD": "ibrd_debt_usd",
    "DT.DOD.MIDA.CD": "ida_debt_usd",
    "DT.TDS.DECT.CD": "total_debt_service_usd",
    "DT.TDS.DPPG.CD": "ppg_debt_service_usd",
    "DT.TDS.MLAT.CD": "multilateral_debt_service_usd",
}


def build_country_features(debt_csv="data/international_debt.csv",
                            reference_csv="data/country_reference.csv"):
    debt = pd.read_csv(debt_csv)
    wide = debt.pivot_table(index=["country_code", "country_name"],
                             columns="indicator_code", values="debt").reset_index()
    wide = wide.rename(columns=INDICATOR_COLUMNS)

    ref = pd.read_csv(reference_csv).rename(columns={
        "DT.DOD.DECT.GN.ZS": "debt_pct_gni",
        "DT.DOD.DSTC.ZS": "short_term_pct_reserves",
        "DT.TDS.DECT.EX.ZS": "debt_service_pct_exports",
    })

    df = wide.merge(ref, on=["country_code", "country_name"], how="left")

    # Debt-composition ratios (share of total external debt stock).
    df["short_term_share"] = df["short_term_debt_usd"] / df["total_debt_usd"]
    df["public_ppg_share"] = df["public_ppg_debt_usd"] / df["total_debt_usd"]
    df["private_png_share"] = df["private_png_debt_usd"] / df["total_debt_usd"]
    df["multilateral_share"] = df["world_bank_debt_usd"] / df["total_debt_usd"]

    # Burden ratios not already in country_reference.
    df["debt_pct_gdp"] = 100 * df["total_debt_usd"] / df["gdp_current_usd"]
    df["debt_service_pct_debt"] = 100 * df["total_debt_service_usd"] / df["total_debt_usd"]
    df["reserves_to_debt"] = df["total_reserves_usd"] / df["total_debt_usd"]
    df["debt_per_capita_usd"] = df["total_debt_usd"] / df["population"]

    return df


def attach_labels(features, labels_csv="data/debt_distress_labels.csv"):
    labels = pd.read_csv(labels_csv)
    labels = labels[labels["risk_rating"] != "Unrated"].copy()
    labels["high_risk"] = labels["risk_rating"].isin(
        ["High", "In debt distress"]
    ).astype(int)

    labeled = features.merge(
        labels[["country_name", "risk_rating", "high_risk"]],
        on="country_name", how="inner",
    )
    return labeled


if __name__ == "__main__":
    features = build_country_features()
    features.to_csv("data/country_features.csv", index=False)
    print(f"data/country_features.csv -- {len(features)} countries, "
          f"{features.shape[1]} columns")

    labeled = attach_labels(features)
    labeled.to_csv("data/labeled_features.csv", index=False)
    print(f"data/labeled_features.csv -- {len(labeled)} labeled countries "
          f"({labeled['high_risk'].sum()} high-risk / "
          f"{(1 - labeled['high_risk']).sum()} not)")
