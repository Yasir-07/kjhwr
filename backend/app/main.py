from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app import cache
from app.analysis import build_comparison, compute_metrics, select_latest_forecasts

CUTOFF_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"


@asynccontextmanager
async def lifespan(app):
    cache.load_data()  # once at startup, so requests never wait for Elexon
    yield


app = FastAPI(title="Wind forecast accuracy", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


@lru_cache(maxsize=64)
def compute_result(cutoff_hour, cutoff_minute):
    """The data is fixed, so each cutoff only needs to be computed once."""
    selected = select_latest_forecasts(cache.get_forecasts(), cutoff_hour, cutoff_minute)
    comparison = build_comparison(cache.get_actuals(), selected)
    rows = comparison.assign(
        startTime=comparison["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        publishTime=comparison["publishTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return {
        "cutoff": f"{cutoff_hour:02d}:{cutoff_minute:02d}",
        "metrics": compute_metrics(comparison),
        "rows": rows.to_dict("records"),
    }


@app.get("/api/comparison")
def comparison(cutoff: str = Query("09:20", pattern=CUTOFF_PATTERN, description="HH:MM, UTC")):
    hour, minute = cutoff.split(":")
    return compute_result(int(hour), int(minute))


# In the Docker image the built React app sits in ./static and is served from the same server.
# On Vercel and in local dev this folder doesn't exist, so nothing is mounted.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
