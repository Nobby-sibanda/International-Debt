"""Load the fetched CSVs into a SQLite database for the SQL analysis layer."""
from __future__ import annotations

import sqlite3
import pandas as pd

DB_PATH = "international_debt.db"


def main():
    debt = pd.read_csv("data/international_debt.csv")
    ref = pd.read_csv("data/country_reference.csv")
    history = pd.read_csv("data/debt_time_series.csv")

    conn = sqlite3.connect(DB_PATH)
    debt.to_sql("international_debt", conn, if_exists="replace", index=False)
    ref.to_sql("country_reference", conn, if_exists="replace", index=False)
    history.to_sql("debt_history", conn, if_exists="replace", index=False)

    conn.execute("CREATE INDEX idx_debt_country ON international_debt(country_code)")
    conn.execute("CREATE INDEX idx_debt_indicator ON international_debt(indicator_code)")
    conn.execute("CREATE INDEX idx_ref_country ON country_reference(country_code)")
    conn.execute("CREATE INDEX idx_hist_country ON debt_history(country_code)")
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) FROM international_debt")
    print("international_debt rows:", cur.fetchone()[0])
    cur = conn.execute("SELECT COUNT(*) FROM country_reference")
    print("country_reference rows:", cur.fetchone()[0])
    cur = conn.execute("SELECT COUNT(*) FROM debt_history")
    print("debt_history rows:", cur.fetchone()[0])
    conn.close()
    print(f"Saved {DB_PATH}")


if __name__ == "__main__":
    main()
