import pandas as pd

from app.analysis import build_comparison, compute_metrics, select_latest_forecasts


def ts(text):
    return pd.Timestamp(text, tz="UTC")


def test_select_picks_latest_before_cutoff():
    forecasts = pd.DataFrame({
        "startTime": [ts("2026-01-10 12:00")] * 4,
        "publishTime": [
            ts("2026-01-09 04:30"),
            ts("2026-01-09 07:30"),
            ts("2026-01-09 09:30"),  # after the 09:20 cutoff
            ts("2026-01-10 11:30"),  # after the target day began
        ],
        "forecast_mw": [100, 200, 300, 400],
    })
    result = select_latest_forecasts(forecasts, 9, 20)
    assert len(result) == 1
    assert result.loc[0, "forecast_mw"] == 200


def test_build_comparison_shares_hourly_forecast_and_signs_error():
    actuals = pd.DataFrame({
        "startTime": [ts("2026-01-10 12:00"), ts("2026-01-10 12:30")],
        "actual_mw": [90, 110],
    })
    selected = pd.DataFrame({
        "startTime": [ts("2026-01-10 12:00")],
        "publishTime": [ts("2026-01-09 07:30")],
        "forecast_mw": [100],
    })
    result = build_comparison(actuals, selected)
    assert list(result["error_mw"]) == [10, -10]  # forecast - actual


def test_compute_metrics():
    comparison = pd.DataFrame({
        "actual_mw": [100, 100, 100, 100],
        "forecast_mw": [110, 90, 120, 80],
        "error_mw": [10, -10, 20, -20],
    })
    m = compute_metrics(comparison)
    assert m["bias_mw"] == 0
    assert m["mae_mw"] == 15
    assert round(m["rmse_mw"], 2) == 15.81
    assert m["mape_pct"] == 15
    assert m["p90_abs_error_mw"] == 20

