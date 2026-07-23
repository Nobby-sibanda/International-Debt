"""Fetch World Bank International Debt Statistics (IDS) data via the public API.

Builds two tables:
  - international_debt: long-format (country, indicator, value) mirroring the
    classic "grouping/totals" SQL teaching schema, sourced live from World Bank
    source=6 (International Debt Statistics) for YEAR.
  - country_reference: per-country GDP, population, region, income level for
    context in the top/bottom-10 analysis.

Source: World Bank Open Data API, https://api.worldbank.org/v2/
License: World Bank data is CC BY-4.0.
"""
from __future__ import annotations

import json
import time
import requests
import pandas as pd

YEAR = "2024"
BASE = "https://api.worldbank.org/v2"

# Confirmed-live World Bank IDS indicators for YEAR (many classic AMT/DIS/INT
# flow indicators have been archived/moved off the public API since the debt
# reporting system was restructured -- these DOD/TDS stock+service indicators
# are the ones that currently return real cross-country data).
DEBT_INDICATORS = [
    "DT.DOD.DECT.CD",   # External debt stocks, total (DOD, current US$)
    "DT.DOD.DPPG.CD",   # External debt stocks, public & publicly guaranteed (PPG)
    "DT.DOD.DSTC.CD",   # External debt stocks, short-term
    "DT.DOD.DPNG.CD",   # External debt stocks, private nonguaranteed (PNG)
    "DT.DOD.MWBG.CD",   # IBRD loans and IDA credits (World Bank Group)
    "DT.DOD.MIBR.CD",   # PPG, IBRD
    "DT.DOD.MIDA.CD",   # PPG, IDA
    "DT.TDS.DECT.CD",   # Debt service on external debt, total (TDS)
    "DT.TDS.DPPG.CD",   # Debt service on PPG external debt
    "DT.TDS.MLAT.CD",   # Multilateral debt service
]

RATIO_INDICATORS = [
    "DT.DOD.DECT.GN.ZS",   # External debt stocks (% of GNI)
    "DT.DOD.DSTC.ZS",      # Short-term debt (% of total external debt)
    "DT.TDS.DECT.EX.ZS",   # Total debt service (% of exports of goods, services & primary income)
]

CONTEXT_INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "SP.POP.TOTL": "population",
    "FI.RES.TOTL.CD": "total_reserves_usd",
}

INDICATOR_NAMES = {}  # filled in as we fetch


def get_countries() -> pd.DataFrame:
    rows = []
    page = 1
    while True:
        r = requests.get(f"{BASE}/country", params={"format": "json", "per_page": 400, "page": page})
        data = r.json()
        for c in data[1]:
            if c["region"]["value"] == "Aggregates" or c["region"]["id"] in ("", "NA"):
                continue  # skip World Bank aggregate rows (regions, income groups)
            rows.append({
                "country_code": c["id"],
                "country_name": c["name"],
                "region": c["region"]["value"],
                "income_level": c["incomeLevel"]["value"],
            })
        if page >= data[0]["pages"]:
            break
        page += 1
    return pd.DataFrame(rows)


def fetch_indicator(indicator: str, year: str) -> pd.DataFrame:
    rows = []
    page = 1
    while True:
        r = requests.get(
            f"{BASE}/country/all/indicator/{indicator}",
            params={"format": "json", "date": year, "per_page": 400, "page": page},
        )
        try:
            data = r.json()
        except ValueError:
            break
        if not isinstance(data, list) or len(data) < 2 or data[1] is None:
            break
        for row in data[1]:
            if row["value"] is None:
                continue
            INDICATOR_NAMES[indicator] = row["indicator"]["value"]
            rows.append({
                "country_code": row["countryiso3code"] or row["country"]["id"],
                "value": row["value"],
            })
        if page >= data[0]["pages"]:
            break
        page += 1
    return pd.DataFrame(rows, columns=["country_code", "value"])


def main():
    print("Fetching country reference list...")
    countries = get_countries()
    print(f"  {len(countries)} countries/economies")
    valid_codes = set(countries["country_code"])

    print(f"Fetching {len(DEBT_INDICATORS)} debt-composition indicators for {YEAR}...")
    long_rows = []
    for ind in DEBT_INDICATORS:
        df = fetch_indicator(ind, YEAR)
        df = df[df["country_code"].isin(valid_codes)]
        for _, row in df.iterrows():
            long_rows.append({
                "country_code": row["country_code"],
                "indicator_code": ind,
                "value": row["value"],
            })
        print(f"  {ind:20s} {INDICATOR_NAMES.get(ind,''):55s} {len(df):4d} countries")
        time.sleep(0.15)

    debt_long = pd.DataFrame(long_rows)
    debt_long = debt_long.merge(countries[["country_code", "country_name"]], on="country_code", how="left")
    debt_long["indicator_name"] = debt_long["indicator_code"].map(INDICATOR_NAMES)
    debt_long = debt_long[["country_name", "country_code", "indicator_name", "indicator_code", "value"]]
    debt_long = debt_long.rename(columns={"value": "debt"})
    debt_long.to_csv("data/international_debt.csv", index=False)
    print(f"Saved data/international_debt.csv  ({len(debt_long)} rows)")

    print(f"Fetching {len(RATIO_INDICATORS)} ratio indicators for {YEAR}...")
    ratio_frames = []
    for ind in RATIO_INDICATORS:
        df = fetch_indicator(ind, YEAR)
        df = df[df["country_code"].isin(valid_codes)][["country_code", "value"]].rename(columns={"value": ind})
        ratio_frames.append(df)
        time.sleep(0.15)

    print("Fetching context indicators (GDP, population, reserves)...")
    ctx_frames = []
    for ind, col in CONTEXT_INDICATORS.items():
        df = fetch_indicator(ind, YEAR)
        df = df[df["country_code"].isin(valid_codes)][["country_code", "value"]].rename(columns={"value": col})
        ctx_frames.append(df)
        time.sleep(0.15)

    ref = countries.copy()
    for df in ratio_frames + ctx_frames:
        ref = ref.merge(df, on="country_code", how="left")

    ref.to_csv("data/country_reference.csv", index=False)
    print(f"Saved data/country_reference.csv  ({len(ref)} rows)")

    with open("data/indicator_glossary.json", "w") as f:
        json.dump(INDICATOR_NAMES, f, indent=2)
    print("Saved data/indicator_glossary.json")
    print(f"\nData year used: {YEAR}")


if __name__ == "__main__":
    main()
