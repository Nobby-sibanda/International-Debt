"""Fetch the full historical time series for total external debt (DT.DOD.DECT.CD)
for every country, to identify the year each country's debt actually peaked.
"""
from __future__ import annotations

import requests
import pandas as pd

BASE = "https://api.worldbank.org/v2"
INDICATOR = "DT.DOD.DECT.CD"


def get_country_codes():
    ref = pd.read_csv("data/country_reference.csv")
    return set(ref.country_code)


def main():
    valid_codes = get_country_codes()
    rows = []
    page = 1
    while True:
        r = requests.get(
            f"{BASE}/country/all/indicator/{INDICATOR}",
            params={"format": "json", "date": "1970:2024", "per_page": 20000, "page": page},
        )
        data = r.json()
        for row in data[1]:
            if row["value"] is None:
                continue
            if row["countryiso3code"] not in valid_codes:
                continue
            rows.append({
                "country_code": row["countryiso3code"],
                "country_name": row["country"]["value"],
                "year": int(row["date"]),
                "debt": row["value"],
            })
        if page >= data[0]["pages"]:
            break
        page += 1

    df = pd.DataFrame(rows)
    df.to_csv("data/debt_time_series.csv", index=False)
    print(f"Saved data/debt_time_series.csv ({len(df)} rows, {df.country_code.nunique()} countries, "
          f"years {df.year.min()}-{df.year.max()})")

    peak = df.loc[df.groupby("country_code")["debt"].idxmax()][["country_name", "country_code", "year", "debt"]]
    peak = peak.sort_values("debt", ascending=False).reset_index(drop=True)
    peak.to_csv("data/peak_debt_year.csv", index=False)
    print(f"Saved data/peak_debt_year.csv ({len(peak)} countries)")


if __name__ == "__main__":
    main()
