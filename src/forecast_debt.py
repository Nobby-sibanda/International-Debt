"""ARIMA forecasts of total external debt for the 10 largest 2024 debtors.

For each country: grid-search a small ARIMA(p,d,q) on log-debt by AIC,
backtest by holding out the last 5 actual years (2020-2024) and scoring
MAPE/RMSE against them, then refit on the full 1970-2024 series and
forecast 2025-2027 with 95% confidence intervals.
"""
import itertools
import json
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")
# statsmodels re-forces these past a blanket filterwarnings("ignore"), so they
# need to be silenced by category explicitly.
warnings.simplefilter("ignore", ValueWarning)
warnings.simplefilter("ignore", ConvergenceWarning)

TOP_10 = ["China", "India", "Brazil", "Mexico", "Turkiye", "Indonesia",
          "Argentina", "Colombia", "Ukraine", "Thailand"]
BACKTEST_YEARS = 5
FORECAST_YEARS = 3
ORDER_GRID = list(itertools.product(range(3), range(2), range(3)))


def best_order(series):
    best_aic, best = np.inf, (1, 1, 0)
    for order in ORDER_GRID:
        try:
            fit = ARIMA(series, order=order).fit()
            if fit.aic < best_aic:
                best_aic, best = fit.aic, order
        except Exception:
            continue
    return best


def fit_and_forecast(series, order, steps):
    fit = ARIMA(series, order=order).fit()
    fc = fit.get_forecast(steps=steps)
    mean = np.exp(fc.predicted_mean)
    ci = np.exp(fc.conf_int(alpha=0.05))
    return mean, ci


def main():
    hist = pd.read_csv("data/debt_time_series.csv")
    results = {}

    fig, axes = plt.subplots(2, 5, figsize=(22, 8), sharex=False)

    for ax, country in zip(axes.flat, TOP_10):
        s = (hist[hist["country_name"] == country]
             .sort_values("year").set_index("year")["debt"])
        log_s = np.log(s)

        train = log_s.iloc[:-BACKTEST_YEARS]
        actual_holdout = s.iloc[-BACKTEST_YEARS:]

        order = best_order(train)
        pred_mean, _ = fit_and_forecast(train, order, BACKTEST_YEARS)
        pred_mean.index = actual_holdout.index

        mape = mean_absolute_percentage_error(actual_holdout, pred_mean)
        rmse = np.sqrt(mean_squared_error(actual_holdout, pred_mean))

        full_order = best_order(log_s)
        future_years = list(range(int(s.index.max()) + 1,
                                   int(s.index.max()) + 1 + FORECAST_YEARS))
        fc_mean, fc_ci = fit_and_forecast(log_s, full_order, FORECAST_YEARS)
        fc_mean.index = future_years
        fc_ci.index = future_years

        results[country] = {
            "backtest_order": list(order),
            "backtest_mape": round(float(mape), 4),
            "backtest_rmse_usd": round(float(rmse), 2),
            "full_order": list(full_order),
            "forecast_years": future_years,
            "forecast_debt_usd": {int(y): round(float(v), 2)
                                   for y, v in fc_mean.items()},
            "forecast_ci_lower_usd": {int(y): round(float(v), 2)
                                       for y, v in fc_ci.iloc[:, 0].items()},
            "forecast_ci_upper_usd": {int(y): round(float(v), 2)
                                       for y, v in fc_ci.iloc[:, 1].items()},
        }

        ax.plot(s.index, s / 1e9, label="actual", color="black", linewidth=1.2)
        ax.plot(pred_mean.index, pred_mean / 1e9, "--", color="tab:orange",
                 label=f"backtest (MAPE={mape:.1%})")
        ax.plot(fc_mean.index, fc_mean / 1e9, "o-", color="tab:blue",
                 label="2025-27 forecast")
        ax.fill_between(fc_ci.index, fc_ci.iloc[:, 0] / 1e9, fc_ci.iloc[:, 1] / 1e9,
                         color="tab:blue", alpha=0.2)
        ax.set_title(country, fontsize=10)
        ax.set_ylabel("US$ billions")
        ax.tick_params(labelsize=8)

    axes.flat[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("External debt: actual (1970-2024), 5-year backtest, "
                 "and 2025-2027 ARIMA forecast -- top 10 debtors")
    fig.tight_layout()
    fig.savefig("models/figures/forecast_top10.png", dpi=150)

    with open("models/forecast_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    avg_mape = np.mean([r["backtest_mape"] for r in results.values()])
    print(f"Average backtest MAPE across top 10: {avg_mape:.1%}")
    for country, r in results.items():
        print(f"  {country}: order={r['backtest_order']}, "
              f"MAPE={r['backtest_mape']:.1%}, "
              f"2027 forecast=${r['forecast_debt_usd'][2027] / 1e9:.1f}B")

    print("\nSaved models/forecast_metrics.json, models/figures/forecast_top10.png")


if __name__ == "__main__":
    main()
