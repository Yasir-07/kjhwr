from app.elexon_client import fetch_actuals, fetch_forecasts

actuals = fetch_actuals()
forecasts = fetch_forecasts()

# Actuals: expect 31 days x 48 half-hours = 1488 rows (2 Jan - 1 Feb)
print("ACTUALS rows:", len(actuals))
print(actuals.head())
print("range:", actuals["startTime"].min(), "->", actuals["startTime"].max())
print("missing values:", actuals["actual_mw"].isna().sum())
print("negative values:", (actuals["actual_mw"] < 0).sum())

# Forecasts: many batches (publishTime), each covering many target hours (startTime)
print("\nFORECASTS rows:", len(forecasts))
print(forecasts.head())
print("publish range:", forecasts["publishTime"].min(), "->", forecasts["publishTime"].max())
print("missing values:", forecasts["forecast_mw"].isna().sum())
print("negative values:", (forecasts["forecast_mw"] < 0).sum())

# Horizon = how many hours ahead of the target time the forecast was made
forecasts["horizon_hours"] = (
    forecasts["startTime"] - forecasts["publishTime"]
).dt.total_seconds() / 3600
print("\nHorizon (hours):")
print(forecasts["horizon_hours"].describe())
print("forecasts published after their target time:", (forecasts["horizon_hours"] < 0).sum())

print("\nForecasts per target time:")
print(forecasts.groupby("startTime").size().describe())

# When does the forecaster publish batches?
publish_times = forecasts["publishTime"].drop_duplicates().sort_values()
print("\nBatches:", len(publish_times))
print("First day's batches:")
print(publish_times.head(8).to_string(index=False))
