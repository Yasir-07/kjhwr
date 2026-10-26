# Wind forecast accuracy: January 2026 day-ahead decisions

A web app for a UK energy utility's day-ahead buying team. It answers two questions using national wind data from Elexon (BMRS) only:

1. **What was the latest wind forecast available when the day-ahead decision had to be made?**
2. **How accurate were those forecasts?** (bias, MAE, RMSE, MAPE and P90 error, in MW)

**Live app:** https://kjhwr-zeta.vercel.app (hosted on Vercel)

**Demo video:** https://youtu.be/HgRrRXpBp0Q

## Use of AI tools

I used **Claude Code** (Anthropic) to assist in building this project, including the code, tests and this README. I reviewed, ran and tested the result myself.

## How it works

Decisions are made once a day, before a cutoff, for delivery the next day. For every delivery day from 2 Jan to 1 Feb 2026 (the days covered by decisions made in January 2026):

1. Take every WINDFOR forecast for that day.
2. Keep only those **published before the cutoff on the previous day**, and take the newest one for each target hour. Forecasts published after the cutoff would not have been available, so they are excluded.
3. Compare it with the FUELHH actual wind generation for the same time and compute the error (`forecast - actual`; positive means the forecast was too high).
4. Summarise the errors over the month.

### Data used

| Dataset | Used for | Fields |
|---|---|---|
| FUELHH (`fuelType=WIND`) | Actual generation, half-hourly | `startTime`, `generation` |
| WINDFOR | Forecasts, hourly, many publish times per target | `startTime`, `publishTime`, `generation` |

### Assumptions

- **Decisions in January 2026:** decisions are made on 1 to 31 Jan, so delivery days run from 2 Jan to 1 Feb. Forecasts published from 1 Jan are fetched. The window is set by constants in `backend/app/elexon_client.py`.
- **Cutoff:** the brief gives none. The app offers the GB day-ahead gate closures, **09:20 (EPEX, default)** and **09:50 (N2EX)**, UK time. Check these against the exchanges' current rules.
- **Time zone:** all times are UTC, which equals UK time in January.
- **Resolution:** forecasts are hourly and actuals half-hourly, so each hourly forecast is applied to both half-hours inside that hour.
- **Percentage error (MAPE)** skips periods where actual output is 0.
- **Scope:** the app measures the wind forecast only. It does not use demand, so it does not say how much to buy.

## Metrics

| Metric | Meaning |
|---|---|
| Bias | Mean of `forecast - actual`. Positive means the forecast is too high. |
| MAE | Mean absolute error. |
| RMSE | Root mean squared error, so large misses weigh more. |
| MAPE | Mean absolute error as a percentage of actual output. |
| P90 error | The absolute error that 90% of half-hours stay below. |

## Project structure

```
.
├── README.md
├── Dockerfile                  Two-stage image: builds the React app, serves it with the API
├── .dockerignore               Keeps dev files out of the image
├── vercel.json                 Vercel build and routing config
├── requirements.txt            Python dependencies used by the Vercel function
├── api/
│   └── index.py                Vercel entry point, exposes the FastAPI app
├── backend/
│   ├── requirements.txt        Python dependencies
│   ├── app/
│   │   ├── elexon_client.py    Fetches and cleans FUELHH and WINDFOR from the Elexon API
│   │   ├── cache.py            Loads the data once (from backend/data/ or Elexon) and keeps it in memory
│   │   ├── analysis.py         Cutoff selection, forecast-vs-actual comparison and metrics
│   │   └── main.py             FastAPI app: GET /api/comparison?cutoff=HH:MM (also serves the built React app in Docker)
│   ├── scripts/
│   │   └── explore.py          Sanity checks on the raw data
│   ├── tests/
│   │   └── test_analysis.py    Unit tests for the analysis functions
│   └── data/                   Saved CSV snapshot of the Elexon data (so the deployed app never calls Elexon)
└── frontend/
    ├── package.json            Node dependencies and scripts
    ├── vite.config.js          Dev server, proxies /api to the backend
    ├── index.html
    └── src/
        ├── main.jsx            React entry point
        ├── App.jsx             Page: state, data loading, layout
        ├── api.js              Fetches /api/comparison, caches responses per cutoff
        ├── components/
        │   ├── MetricCards.jsx The five accuracy cards
        │   └── ForecastChart.jsx Forecast-vs-actual chart (day and month views)
        ├── App.css             Page styles
        └── index.css           Colour tokens and light/dark theme
```

## API

`GET /api/comparison?cutoff=HH:MM` (UTC, default `09:20`)

```json
{
  "cutoff": "09:20",
  "metrics": { "bias_mw": 0, "mae_mw": 0, "rmse_mw": 0, "mape_pct": 0, "p90_abs_error_mw": 0, "count": 1488 },
  "rows": [
    { "startTime": "2026-01-02T00:00:00Z", "actual_mw": 0, "publishTime": "2026-01-01T07:30:00Z",
      "forecast_mw": 0, "horizon_hours": 0, "error_mw": 0 }
  ]
}
```

An invalid cutoff returns `422`. Interactive docs are at `/docs` when the backend is running.

## Running locally

Requirements: Python 3.11+ and Node 20+.

**Backend** (terminal 1):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://localhost:8000
```

The data is read from the CSV snapshot in `backend/data/`. If those files are missing, the app downloads the data from Elexon (a couple of seconds) and saves them. Delete `backend/data/` to fetch fresh data.

**Frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000`.

### Tests

```bash
cd backend
pip install pytest
python -m pytest -q
```

## Deployment (Vercel)

The live app runs on Vercel. `vercel.json` builds the React app into `frontend/dist` and serves it as static files. `api/index.py` runs the FastAPI app as a serverless function behind `/api/*`.

Because a serverless function starts fresh and has a read-only disk, the Elexon data is committed as a CSV snapshot in `backend/data/` and loaded into memory on the first request. The deployed app never calls Elexon.

To redeploy, run from the repository root:

```bash
npx vercel --prod
```

The first request after the app has been idle can take a few seconds while the function starts.

## Running with Docker

The image builds the React app and serves it together with the API from one container.

```bash
docker build -t kjhwr .
docker run --rm -p 8080:8000 kjhwr
```

Then open http://localhost:8080 (API docs at http://localhost:8080/docs). The Elexon data snapshot is baked into the image, so the container needs no network access.

The `Dockerfile` has two stages: a Node stage that runs `npm run build`, and a slim Python stage that installs `requirements.txt`, copies the backend and the built front end, and runs `uvicorn` as a non-root user. The server listens on the `PORT` environment variable (default 8000).

## Performance notes

- Elexon is called once; the cleaned data is held in memory and saved to disk, so requests never wait for the API (about 2 s from Elexon, about 5 ms from the saved CSVs).
- The forecast selection is vectorised pandas (no Python loops over rows).
- Results are cached per cutoff in the backend, and responses are gzip-compressed (about 220 KB to 19 KB).
- The frontend makes one request per cutoff and caches it, so switching delivery day or going back to a cutoff makes no request. Chart code is loaded lazily, and chart animation is off.
