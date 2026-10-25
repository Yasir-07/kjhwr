import time

import pandas as pd
import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Decisions are made in January 2026 (for delivery on 2 Jan - 1 Feb)
FORECAST_PUBLISH_FROM = "2026-01-01T00:00:00Z"
FORECAST_PUBLISH_TO = "2026-02-01T00:00:00Z"
ACTUALS_FROM = "2026-01-02"
ACTUALS_TO = "2026-02-01"


def _get(dataset, params):
    """Call the Elexon stream endpoint, trying up to 3 times."""
    for attempt in range(3):
        try:
            resp = requests.get(f"{BASE_URL}/{dataset}/stream", params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(1)


def fetch_actuals():
    rows = _get("FUELHH", {
        "settlementDateFrom": ACTUALS_FROM,
        "settlementDateTo": ACTUALS_TO,
        "fuelType": "WIND",
    })
    df = pd.DataFrame(rows)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df[["startTime", "generation"]].rename(columns={"generation": "actual_mw"})
    return df.drop_duplicates("startTime").sort_values("startTime").reset_index(drop=True)


def fetch_forecasts():
    rows = _get("WINDFOR", {
        "publishDateTimeFrom": FORECAST_PUBLISH_FROM,
        "publishDateTimeTo": FORECAST_PUBLISH_TO,
    })
    df = pd.DataFrame(rows)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df[["startTime", "publishTime", "generation"]].rename(columns={"generation": "forecast_mw"})
    return df.drop_duplicates(["startTime", "publishTime"]).sort_values(["startTime", "publishTime"]).reset_index(drop=True)
