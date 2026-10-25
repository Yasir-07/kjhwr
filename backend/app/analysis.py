import pandas as pd


def select_latest_forecasts(forecasts, cutoff_hour=9, cutoff_minute=20):
    """For each target time, keep the newest forecast published before the
    day-ahead cutoff (the day before the target, at cutoff_hour:cutoff_minute UTC)."""
    # Deadline for each row: the day before its target day, at the cutoff time
    deadline = (
        forecasts["startTime"].dt.normalize()
        - pd.Timedelta(days=1)
        + pd.Timedelta(hours=cutoff_hour, minutes=cutoff_minute)
    )

    allowed = forecasts[forecasts["publishTime"] <= deadline]

    # Newest allowed forecast per target time
    return (
        allowed.sort_values(["startTime", "publishTime"])
        .drop_duplicates("startTime", keep="last")
        .reset_index(drop=True)
    )


def build_comparison(actuals, selected_forecasts):
    """Put each half-hour actual next to the forecast for its hour and add the error.
    Forecasts are hourly, so both half-hours of an hour share one forecast."""
    comparison = actuals.copy()
    comparison["hour"] = comparison["startTime"].dt.floor("h")

    forecasts = selected_forecasts.rename(columns={"startTime": "hour"})
    comparison = comparison.merge(forecasts, on="hour", how="inner")

    # Positive error = forecast was too high
    comparison["error_mw"] = comparison["forecast_mw"] - comparison["actual_mw"]
    return comparison.drop(columns="hour")


def compute_metrics(comparison):
    """Summary numbers describing how wrong the forecasts were."""
    error = comparison["error_mw"]
    abs_error = error.abs()

    # % error is undefined when actual output is 0, so skip those rows
    nonzero = comparison["actual_mw"] != 0
    pct_error = abs_error[nonzero] / comparison.loc[nonzero, "actual_mw"] * 100

    return {
        "bias_mw": float(error.mean()),
        "mae_mw": float(abs_error.mean()),
        "rmse_mw": float((error ** 2).mean() ** 0.5),
        "mape_pct": float(pct_error.mean()),
        "p90_abs_error_mw": float(abs_error.quantile(0.9)),
        "count": int(len(comparison)),
    }


def _summarise(groups):
    return groups.agg(
        bias_mw=("error_mw", "mean"),
        mae_mw=("abs_error_mw", "mean"),
        avg_actual_mw=("actual_mw", "mean"),
    ).reset_index()


def error_by_hour(comparison):
    """Bias and MAE for each hour of the day (UTC, same as UK time in January)."""
    df = comparison.assign(abs_error_mw=comparison["error_mw"].abs())
    return _summarise(df.groupby(df["startTime"].dt.hour.rename("hour")))


def error_by_day(comparison):
    """Bias and MAE for each delivery day."""
    df = comparison.assign(abs_error_mw=comparison["error_mw"].abs())
    return _summarise(df.groupby(df["startTime"].dt.strftime("%Y-%m-%d").rename("date")))

