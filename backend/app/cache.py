from pathlib import Path

import pandas as pd

from app.elexon_client import fetch_actuals, fetch_forecasts

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUALS_FILE = DATA_DIR / "actuals.csv"
FORECASTS_FILE = DATA_DIR / "forecasts.csv"

_actuals = None
_forecasts = None


def load_data():
    """Fill the in-memory tables from the saved CSVs, or from Elexon if they don't exist."""
    global _actuals, _forecasts

    if ACTUALS_FILE.exists() and FORECASTS_FILE.exists():
        _actuals = pd.read_csv(ACTUALS_FILE, parse_dates=["startTime"])
        _forecasts = pd.read_csv(FORECASTS_FILE, parse_dates=["startTime", "publishTime"])
    else:
        _actuals = fetch_actuals()
        _forecasts = fetch_forecasts()
        try:
            DATA_DIR.mkdir(exist_ok=True)
            _actuals.to_csv(ACTUALS_FILE, index=False)
            _forecasts.to_csv(FORECASTS_FILE, index=False)
        except OSError:
            pass  # read-only filesystem (e.g. serverless); keep the data in memory only

    _forecasts["horizon_hours"] = (
        _forecasts["startTime"] - _forecasts["publishTime"]
    ).dt.total_seconds() / 3600


def get_actuals():
    if _actuals is None:
        load_data()
    return _actuals


def get_forecasts():
    if _forecasts is None:
        load_data()
    return _forecasts
