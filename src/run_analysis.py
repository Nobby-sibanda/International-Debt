"""Execute sql/analysis.sql query-by-query against international_debt.db,
printing and saving each result set. Splits on the '-- N.' numbered comment
markers in the .sql file.
"""
from __future__ import annotations

import re
import sqlite3
import pandas as pd

conn = sqlite3.connect("international_debt.db")

sql_text = open("sql/analysis.sql").read()
# Split into numbered blocks like "-- 1. ..." through the next "-- N."
blocks = re.split(r"\n(?=-- \d+\. )", sql_text)
blocks = [b for b in blocks if re.match(r"-- \d+\. ", b.strip())]

results_dir = "data/analysis_results"
import os
os.makedirs(results_dir, exist_ok=True)

summary_lines = []
for block in blocks:
    header_match = re.match(r"-- (\d+)\. (.+)", block.strip())
    num, title = header_match.group(1), header_match.group(2)
    query = block[block.index(";", block.index("SELECT")) - 0:]  # not used
    # extract the actual SQL (from first SELECT to trailing ;)
    sql_start = block.index("SELECT")
    query = block[sql_start:].strip()
    df = pd.read_sql_query(query, conn)
    fname = f"{results_dir}/{num.zfill(2)}_{re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:50]}.csv"
    df.to_csv(fname, index=False)
    print(f"\n=== Query {num}: {title} ===")
    print(df.to_string(index=False))
    summary_lines.append(f"Query {num} -> {fname}  ({len(df)} rows)")

print("\n\n--- SAVED ---")
for l in summary_lines:
    print(l)

conn.close()
