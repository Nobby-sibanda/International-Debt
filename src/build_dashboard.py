"""Build the standalone interactive HTML dashboard for the International Debt
project. Pulls all figures from international_debt.db (SQL) + country_reference,
renders with Plotly, and assembles a self-contained page with KPI cards and a
captioned/sourced description under every chart.
"""
from __future__ import annotations

import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

YEAR = 2024
SOURCE = f"World Bank International Debt Statistics (IDS), {YEAR} data, api.worldbank.org"

# ---- palette (validated categorical + sequential, light surface) ----------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GREEN = "#008300"
VIOLET = "#4a3aa7"
RED = "#e34948"
CATEGORICAL = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

pio.templates.default = None

BASE_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=INK_PRIMARY, size=13),
    margin=dict(l=10, r=40, t=10, b=40),
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor=GRID),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#c3c2b7",
               tickfont=dict(color=INK_SECONDARY, size=12), automargin=True),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#c3c2b7",
               tickfont=dict(color=INK_PRIMARY, size=12.5), automargin=True, ticklabelposition="outside"),
)


def style(fig, **kw):
    layout = {**BASE_LAYOUT, **kw}
    fig.update_layout(**layout)
    return fig


def to_div(fig, cid):
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, div_id=cid, config={"displaylogo": False, "responsive": True})


def main():
    conn = sqlite3.connect("international_debt.db")

    debt = pd.read_sql_query("SELECT * FROM international_debt", conn)
    ref = pd.read_sql_query("SELECT * FROM country_reference", conn)
    total_debt = debt[debt.indicator_code == "DT.DOD.DECT.CD"][["country_name", "country_code", "debt"]]

    charts = {}

    # ---- KPI numbers -------------------------------------------------------
    kpi = {
        "n_countries": debt.country_name.nunique(),
        "n_indicators": debt.indicator_code.nunique(),
        "total_debt_trn": total_debt.debt.sum() / 1e12,
        "top_country": total_debt.sort_values("debt", ascending=False).iloc[0]["country_name"],
        "top_debt_bn": total_debt.sort_values("debt", ascending=False).iloc[0]["debt"] / 1e9,
        "avg_debt_bn": total_debt.debt.mean() / 1e9,
    }

    # ---- 1. Top 10 by total external debt ----------------------------------
    top10 = total_debt.sort_values("debt", ascending=False).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=top10.debt / 1e9, y=top10.country_name, orientation="h",
        marker_color=BLUE, marker_line_width=0,
        text=[f"${v:,.0f}B" for v in top10.debt / 1e9], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Total external debt: $%{x:,.1f}B<extra></extra>",
    ))
    style(fig, height=420, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Total external debt (US$ billions)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["top10"] = to_div(fig, "chart-top10")

    # ---- 2. Bottom 10 by total external debt --------------------------------
    bottom10 = total_debt.sort_values("debt", ascending=True).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=bottom10.debt / 1e9, y=bottom10.country_name, orientation="h",
        marker_color=ORANGE, marker_line_width=0,
        text=[f"${v:,.3f}B" for v in bottom10.debt / 1e9], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Total external debt: $%{x:,.3f}B<extra></extra>",
    ))
    style(fig, height=420, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Total external debt (US$ billions)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["bottom10"] = to_div(fig, "chart-bottom10")

    # ---- 3. Total debt by region --------------------------------------------
    region = debt[debt.indicator_code == "DT.DOD.DECT.CD"].merge(ref[["country_code", "region"]], on="country_code")
    region_g = region.groupby("region", as_index=False).debt.sum().sort_values("debt", ascending=True)
    fig = go.Figure(go.Bar(
        x=region_g.debt / 1e9, y=region_g.region, orientation="h",
        marker_color=BLUE, marker_line_width=0,
        text=[f"${v:,.0f}B" for v in region_g.debt / 1e9], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Total external debt: $%{x:,.1f}B<extra></extra>",
    ))
    style(fig, height=340, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Total external debt (US$ billions)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["region"] = to_div(fig, "chart-region")

    # ---- 4. Total debt by income level --------------------------------------
    inc = debt[debt.indicator_code == "DT.DOD.DECT.CD"].merge(ref[["country_code", "income_level"]], on="country_code")
    inc_g = inc.groupby("income_level", as_index=False).debt.sum().sort_values("debt", ascending=True)
    fig = go.Figure(go.Bar(
        x=inc_g.debt / 1e9, y=inc_g.income_level, orientation="h",
        marker_color=AQUA, marker_line_width=0,
        text=[f"${v:,.0f}B" for v in inc_g.debt / 1e9], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Total external debt: $%{x:,.1f}B<extra></extra>",
    ))
    style(fig, height=260, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Total external debt (US$ billions)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["income"] = to_div(fig, "chart-income")

    # ---- 5. Top 10 by debt-to-GNI ratio -------------------------------------
    gni = ref.dropna(subset=["DT.DOD.DECT.GN.ZS"]).sort_values("DT.DOD.DECT.GN.ZS", ascending=False).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=gni["DT.DOD.DECT.GN.ZS"], y=gni.country_name, orientation="h",
        marker_color=VIOLET, marker_line_width=0,
        text=[f"{v:,.0f}%" for v in gni["DT.DOD.DECT.GN.ZS"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>External debt: %{x:.1f}% of GNI<extra></extra>",
    ))
    style(fig, height=420, xaxis=dict(**BASE_LAYOUT["xaxis"], title="External debt stocks (% of GNI)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["gni_ratio"] = to_div(fig, "chart-gni")

    # ---- 6. Top 10 by debt service as % of exports --------------------------
    tds = ref.dropna(subset=["DT.TDS.DECT.EX.ZS"]).sort_values("DT.TDS.DECT.EX.ZS", ascending=False).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=tds["DT.TDS.DECT.EX.ZS"], y=tds.country_name, orientation="h",
        marker_color=RED, marker_line_width=0,
        text=[f"{v:,.0f}%" for v in tds["DT.TDS.DECT.EX.ZS"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Debt service: %{x:.1f}% of exports<extra></extra>",
    ))
    style(fig, height=420, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Total debt service (% of exports of goods, services & primary income)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["tds_ratio"] = to_div(fig, "chart-tds")

    # ---- 7. Debt vs GDP bubble (top 20 debtors) ------------------------------
    top20 = total_debt.sort_values("debt", ascending=False).head(20).merge(
        ref[["country_code", "gdp_current_usd", "DT.DOD.DECT.GN.ZS"]], on="country_code")
    top20["debt_pct_gdp"] = 100 * top20.debt / top20.gdp_current_usd
    label_set = {"China", "Ukraine", "India", "Mexico", "Colombia", "Turkiye"}
    fig = go.Figure(go.Scatter(
        x=top20.gdp_current_usd / 1e9, y=top20.debt / 1e9, mode="markers+text",
        marker=dict(size=(top20.debt_pct_gdp.clip(5, 110)) * 0.9, color=BLUE, opacity=0.75,
                    line=dict(width=1, color="white")),
        text=[n if n in label_set else "" for n in top20.country_name],
        textposition="top center", textfont=dict(size=11, color=INK_SECONDARY),
        customdata=top20[["country_name", "debt_pct_gdp"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>GDP: $%{x:,.0f}B<br>External debt: $%{y:,.0f}B<br>Debt/GDP: %{customdata[1]:.1f}%<extra></extra>",
    ))
    style(fig, height=440,
          xaxis=dict(**BASE_LAYOUT["xaxis"], title="GDP (US$ billions, log scale)", type="log"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title="Total external debt (US$ billions, log scale)", type="log"))
    charts["debt_vs_gdp"] = to_div(fig, "chart-scatter")

    # ---- 8. Debt composition of the single most-indebted country (China) ----
    top_country_code = total_debt.sort_values("debt", ascending=False).iloc[0]["country_code"]
    comp = debt[(debt.country_code == top_country_code) & (debt.debt > 0)].sort_values("debt", ascending=True)
    short_names = {
        "External debt stocks, total (DOD, current US$)": "Total external debt stock",
        "External debt stocks, short-term (DOD, current US$)": "Short-term debt",
        "External debt stocks, private nonguaranteed (PNG) (DOD, current US$)": "Private nonguaranteed (PNG)",
        "External debt stocks, public and publicly guaranteed (PPG) (DOD, current US$)": "Public & publicly guaranteed (PPG)",
        "Debt service on external debt, total (TDS, current US$)": "Total debt service (annual)",
        "Debt service on external debt, public and publicly guaranteed (PPG) (TDS, current US$)": "PPG debt service (annual)",
        "IBRD loans and IDA credits (DOD, current US$)": "IBRD + IDA (World Bank Group)",
        "PPG, IBRD (DOD, current US$)": "PPG, IBRD",
        "Multilateral debt service (TDS, current US$)": "Multilateral debt service",
        "PPG, IDA (DOD, current US$)": "PPG, IDA",
    }
    comp["label"] = comp.indicator_name.map(short_names).fillna(comp.indicator_name)
    fig = go.Figure(go.Bar(
        x=comp.debt / 1e9, y=comp.label, orientation="h",
        marker_color=CATEGORICAL[: len(comp)][::-1], marker_line_width=0,
        text=[f"${v:,.0f}B" for v in comp.debt / 1e9], textposition="outside",
        hovertemplate="<b>%{y}</b><br>$%{x:,.1f}B<extra></extra>",
    ))
    style(fig, height=380, xaxis=dict(**BASE_LAYOUT["xaxis"], title="US$ billions"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["composition"] = to_div(fig, "chart-composition")
    kpi["composition_country"] = debt[debt.country_code == top_country_code].country_name.iloc[0]

    # ---- 9. World map: average debt per country (GROUP BY country, AVG) ----
    avg_debt = debt.groupby(["country_code", "country_name"], as_index=False).agg(
        avg_debt=("debt", "mean"), n_indicators=("debt", "count"))
    log_z = np.log10(avg_debt.avg_debt.clip(lower=1))
    fig = go.Figure(go.Choropleth(
        locations=avg_debt.country_code, z=log_z, locationmode="ISO-3",
        customdata=avg_debt[["country_name", "n_indicators", "avg_debt"]].values,
        colorscale=[[0, "#cde2fb"], [0.25, "#6da7ec"], [0.5, "#2a78d6"], [0.75, "#1c5cab"], [1, "#0d366b"]],
        zmin=log_z.min(), zmax=log_z.max(),
        colorbar=dict(title="Avg debt", tickfont=dict(color=INK_SECONDARY, size=11),
                       outlinewidth=0, len=0.8,
                       tickvals=[7, 8, 9, 10, 11], ticktext=["$10M", "$100M", "$1B", "$10B", "$100B"]),
        marker_line_color="white", marker_line_width=0.5,
        hovertemplate="<b>%{customdata[0]}</b><br>Average debt: $%{customdata[2]:,.0f}<br>Across %{customdata[1]} indicators<extra></extra>",
    ))
    fig.update_geos(bgcolor=SURFACE, showframe=False, showcoastlines=False,
                     landcolor="#eceae4", lakecolor=SURFACE, projection_type="natural earth")
    style(fig, height=460, margin=dict(l=0, r=0, t=0, b=0))
    charts["world_map"] = to_div(fig, "chart-worldmap")

    # ---- 10. Peak historical debt year -- top 10 most-indebted countries ---
    peak = pd.read_csv("data/peak_debt_year.csv")
    top10_names = total_debt.sort_values("debt", ascending=False).head(10).country_name.tolist()
    peak_top10 = peak[peak.country_name.isin(top10_names)].copy()
    peak_top10["order"] = peak_top10.country_name.map({n: i for i, n in enumerate(top10_names)})
    peak_top10 = peak_top10.sort_values("order", ascending=False)
    is_2024 = peak_top10.year == 2024
    fig = go.Figure(go.Bar(
        x=peak_top10.debt / 1e9, y=peak_top10.country_name, orientation="h",
        marker_color=[ORANGE if y else BLUE for y in is_2024], marker_line_width=0,
        text=[f"{yr} · ${v:,.0f}B" for yr, v in zip(peak_top10.year, peak_top10.debt / 1e9)],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Peak year: " + peak_top10.year.astype(str) + "<br>Peak debt: $%{x:,.1f}B<extra></extra>",
    ))
    style(fig, height=420, xaxis=dict(**BASE_LAYOUT["xaxis"], title="Historical peak external debt (US$ billions)"),
          yaxis=dict(**BASE_LAYOUT["yaxis"], title=None))
    charts["peak_year"] = to_div(fig, "chart-peakyear")

    conn.close()
    return kpi, charts, {
        "top10_table": top10.iloc[::-1][["country_name"]].country_name.tolist(),
        "bottom10_table": bottom10.iloc[::-1][["country_name"]].country_name.tolist(),
    }


PANEL = """
<section class="panel{wide_class}">
  <h2>{title}</h2>
  {div}
  <p class="caption">{caption} <span class="source">Source: {source}</span></p>
</section>
"""


def panel(title, div, caption, source, wide=False):
    return PANEL.format(title=title, div=div, caption=caption, source=source,
                         wide_class=" wide" if wide else "")

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>International Debt — Interactive Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    color-scheme: light;
    --surface-1: #fcfcfb;
    --page: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --grid: #e1e0d9;
    --border: rgba(11,11,11,0.10);
    --blue: #2a78d6;
    --orange: #eb6834;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1: #232322;
      --page: #0d0d0d;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #898781;
      --grid: #2c2c2a;
      --border: rgba(255,255,255,0.10);
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1: #232322;
    --page: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --grid: #2c2c2a;
    --border: rgba(255,255,255,0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--page); color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  header {{ padding: 28px 24px 8px; max-width: 1180px; margin: 0 auto; }}
  header h1 {{ margin: 0 0 4px; font-size: 1.7rem; }}
  header p {{ margin: 0; color: var(--text-secondary); }}
  .kpis {{
    max-width: 1180px; margin: 20px auto 0; padding: 0 24px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;
  }}
  .kpi {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px 16px;
  }}
  .kpi .label {{ font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .03em; }}
  .kpi .value {{ font-size: 1.5rem; font-weight: 600; margin-top: 4px; }}
  main {{
    max-width: 1180px; margin: 24px auto 60px; padding: 0 24px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 20px;
  }}
  .panel.wide {{ grid-column: 1 / -1; }}
  .panel {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 20px 16px;
  }}
  .panel h2 {{ margin: 0 0 10px; font-size: 1.05rem; }}
  .panel .caption {{
    margin: 12px 0 0; font-size: 0.86rem; color: var(--text-secondary); line-height: 1.45;
  }}
  .panel .source {{ display: block; margin-top: 4px; color: var(--text-muted); font-size: 0.78rem; }}
  footer {{
    max-width: 1180px; margin: 0 auto 40px; padding: 0 24px; color: var(--text-muted); font-size: 0.82rem;
  }}
  a {{ color: var(--blue); }}
</style>
</head>
<body>
<header>
  <h1>International Debt — World Bank Statistics ({year})</h1>
  <p>Interactive exploration of external debt across {n_countries} countries — grouping, totals, and
  cross-country comparisons drawn from a SQL analysis layer. Hover any chart for exact values.</p>
</header>

<div class="kpis">
  <div class="kpi"><div class="label">Countries covered</div><div class="value">{n_countries}</div></div>
  <div class="kpi"><div class="label">Debt indicators tracked</div><div class="value">{n_indicators}</div></div>
  <div class="kpi"><div class="label">Combined external debt</div><div class="value">${total_debt_trn:.2f}T</div></div>
  <div class="kpi"><div class="label">Largest single debtor</div><div class="value">{top_country}</div></div>
  <div class="kpi"><div class="label">{top_country}'s total debt</div><div class="value">${top_debt_bn:,.0f}B</div></div>
  <div class="kpi"><div class="label">Average debt / country</div><div class="value">${avg_debt_bn:,.1f}B</div></div>
</div>

<main>
{panels}
</main>

<footer>
  Built with Python (pandas), SQLite, and Plotly from World Bank Open Data (CC BY-4.0). See the
  <a href="../README.md">README</a> for the full methodology, SQL queries, and country-level cause analysis.
</footer>
</body>
</html>
"""


def render_page(kpi, charts):
    panels = []
    panels.append(panel(
        title="Top 10 Countries by Total External Debt",
        div=charts["top10"],
        caption=("Countries ranked by total external debt stock in absolute US dollars. Large, "
                  "industrializing economies dominate this list simply because they borrow (and owe) "
                  "at a scale proportional to the size of their economies — see the GDP comparison "
                  "panel below for a size-adjusted view."),
        source="World Bank IDS, indicator DT.DOD.DECT.CD (External debt stocks, total, DOD, current US$), 2024",
        wide=True,
    ))
    panels.append(panel(
        title="Bottom 10 Countries by Total External Debt",
        div=charts["bottom10"],
        caption=("The 10 countries with the smallest external debt stock in absolute dollar terms — "
                  "almost entirely small island and micro-economies. A low dollar figure here mostly "
                  "reflects a tiny economy and limited access to international capital markets, not "
                  "necessarily prudent debt management; several of these carry a high debt burden "
                  "relative to their own small GDP (see the country notes in the README)."),
        source="World Bank IDS, indicator DT.DOD.DECT.CD (External debt stocks, total, DOD, current US$), 2024",
        wide=True,
    ))
    panels.append(panel(
        title="World Map — Average External Debt per Country",
        div=charts["world_map"],
        caption=("Choropleth of each country's own average debt across all reported indicators (total "
                  "stock, short-term, PPG, PNG, debt service, etc.) — i.e. GROUP BY country, AVG(debt). "
                  "Color uses a log scale since a handful of large economies are hundreds of times "
                  "bigger than most others. Hover any country for its exact average and the number of "
                  "indicators that average is drawn from."),
        source="World Bank IDS, all DT.DOD.* / DT.TDS.* indicators, averaged per country, 2024",
        wide=True,
    ))
    panels.append(panel(
        title="Total External Debt by World Bank Region",
        div=charts["region"],
        caption=("External debt stock summed across all reporting countries in each region. East Asia "
                  "& Pacific and Latin America & the Caribbean carry the largest combined debt loads, "
                  "driven by a small number of large middle-income economies (China, Brazil, Mexico) "
                  "rather than a broad regional pattern."),
        source="World Bank IDS, indicator DT.DOD.DECT.CD, joined to World Bank country region classification, 2024",
    ))
    panels.append(panel(
        title="Total External Debt by Income Level",
        div=charts["income"],
        caption=("Upper-middle-income countries hold the largest combined external debt stock, more "
                  "than 3x lower-middle-income countries and over 20x low-income countries — a reminder "
                  "that in absolute dollars, debt tracks market access and economic size more than "
                  "poverty. Low-income countries borrow far less in total but often at far less "
                  "favorable, less sustainable terms relative to their economies."),
        source="World Bank IDS + World Bank income-group classification, 2024",
    ))
    panels.append(panel(
        title="Top 10 by External Debt as % of GNI",
        div=charts["gni_ratio"],
        caption=("A size-adjusted view: external debt relative to Gross National Income. Mozambique's "
                  "external debt exceeds 3.5x its entire national income. This ratio — not the raw "
                  "dollar figure — is what the IMF/World Bank Debt Sustainability Framework actually "
                  "uses to flag debt distress risk."),
        source="World Bank IDS, indicator DT.DOD.DECT.GN.ZS (External debt stocks, % of GNI), 2024",
        wide=True,
    ))
    panels.append(panel(
        title="Top 10 by Debt Service as % of Exports",
        div=charts["tds_ratio"],
        caption=("Share of a country's annual export earnings (goods, services & primary income) "
                  "consumed just by debt repayments (principal + interest). El Salvador and Haiti "
                  "spend the largest share of their hard-currency export income servicing debt, "
                  "leaving less room for imports, reserves, or development spending."),
        source="World Bank IDS, indicator DT.TDS.DECT.EX.ZS (Total debt service, % of exports), 2024",
        wide=True,
    ))
    panels.append(panel(
        title="Debt vs. GDP — Top 20 Debtor Countries",
        div=charts["debt_vs_gdp"],
        caption=("Each bubble is a country among the top 20 largest debtors; both axes are log-scaled "
                  "(GDP and debt span several orders of magnitude). Bubble size is debt as a share of "
                  "GDP. Ukraine stands out furthest above the trend line — the only economy here whose "
                  "external debt exceeds its entire annual GDP, a direct consequence of financing the "
                  "war against Russia's invasion since 2022."),
        source="World Bank IDS (DT.DOD.DECT.CD) joined to World Bank national accounts (NY.GDP.MKTP.CD), 2024",
    ))
    composition_country = kpi.get("composition_country", "the top debtor")
    panels.append(panel(
        title=f"Debt Composition — {composition_country} (Largest Debtor)",
        div=charts["composition"],
        caption=(f"Breakdown of {composition_country}'s external debt by instrument type. Short-term "
                  "debt (due within a year) makes up more than half of the total stock — a structural "
                  "risk factor, since short-term debt must be rolled over constantly and is far more "
                  "exposed to sudden shifts in investor confidence or global interest rates than "
                  "long-term public debt."),
        source="World Bank IDS, all DT.DOD.* / DT.TDS.* indicators for this country, 2024",
    ))
    panels.append(panel(
        title="Top 10 Most-Indebted Countries — Year of Peak Historical Debt",
        div=charts["peak_year"],
        caption=("For each of the top 10 most-indebted countries (by 2024 external debt stock), the "
                  "year its total external debt actually peaked historically, and the debt level that "
                  "year. Several countries' historical peak is 2024 itself (debt is still climbing); "
                  "others peaked earlier and have since paid down or restructured. See the README's "
                  "Country Deep Dive for the specific crisis or event tied to each peak year."),
        source="World Bank IDS, indicator DT.DOD.DECT.CD, full available time series per country",
        wide=True,
    ))

    html = PAGE_TEMPLATE.format(
        year=YEAR,
        n_countries=kpi["n_countries"],
        n_indicators=kpi["n_indicators"],
        total_debt_trn=kpi["total_debt_trn"],
        top_country=kpi["top_country"],
        top_debt_bn=kpi["top_debt_bn"],
        avg_debt_bn=kpi["avg_debt_bn"],
        panels="\n".join(panels),
    )
    return html


if __name__ == "__main__":
    kpi, charts, extra = main()
    html = render_page(kpi, charts)
    with open("assets/international_debt_dashboard.html", "w") as f:
        f.write(html)
    print("Wrote assets/international_debt_dashboard.html")
    print("KPIs:", kpi)
