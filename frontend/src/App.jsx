import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { fetchComparison } from './api'
import MetricCards from './components/MetricCards'
import './App.css'

// Charts (and the charting library) load after the page shell and numbers.
const ForecastChart = lazy(() => import('./components/ForecastChart'))

const CUTOFFS = [
  { value: '09:20', label: '09:20 (EPEX)' },
  { value: '09:50', label: '09:50 (N2EX)' },
]

const formatPublish = (iso) =>
  `${Number(iso.slice(8, 10))} ${new Date(iso).toLocaleString('en-GB', { month: 'short', timeZone: 'UTC' })} ${iso.slice(11, 16)}`

export default function App() {
  const [cutoff, setCutoff] = useState(CUTOFFS[0].value)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [day, setDay] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    fetchComparison(cutoff, controller.signal)
      .then((d) => {
        setError(null)
        setData(d)
      })
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
    return () => controller.abort()
  }, [cutoff])

  // Prepared once per response: chart points, grouped by delivery day.
  const { days, byDay, monthPoints } = useMemo(() => {
    if (!data) return { days: [], byDay: new Map(), monthPoints: [] }
    const byDay = new Map()
    const monthPoints = data.rows.map((r) => {
      const date = r.startTime.slice(0, 10)
      const point = {
        label: r.startTime.slice(5, 16).replace('T', ' '),
        time: r.startTime.slice(11, 16),
        actual: r.actual_mw,
        forecast: r.forecast_mw,
        publishTime: r.publishTime,
      }
      if (!byDay.has(date)) byDay.set(date, [])
      byDay.get(date).push(point)
      return point
    })
    return { days: [...byDay.keys()], byDay, monthPoints }
  }, [data])

  const selectedDay = day && byDay.has(day) ? day : days[0]
  const dayPoints = useMemo(
    () => (byDay.get(selectedDay) ?? []).map((p) => ({ ...p, label: p.time })),
    [byDay, selectedDay],
  )

  return (
    <main>
      <header className="top">
        <div>
          <p className="eyebrow">UK day-ahead market · national wind</p>
          <h1>Wind forecast accuracy</h1>
          <p className="sub">January 2026 purchase decisions: what the forecast said, and how far off it was.</p>
        </div>
        <label className="field">
          <span>Decision cutoff</span>
          <select value={cutoff} onChange={(e) => setCutoff(e.target.value)}>
            {CUTOFFS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </label>
      </header>

      {error && <p className="error">Could not load data: {error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}

      {data && (
        <>
          <MetricCards metrics={data.metrics} />

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Forecast available at decision time</h2>
                {dayPoints.length > 0 && (
                  <p className="note">
                    Latest forecast before the {data.cutoff} cutoff the day before, published{' '}
                    <strong>{formatPublish(dayPoints[0].publishTime)} UTC</strong>
                  </p>
                )}
              </div>
              <label className="field">
                <span>Delivery day</span>
                <select value={selectedDay} onChange={(e) => setDay(e.target.value)}>
                  {days.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>
            </div>
            <Suspense fallback={<p className="muted">Loading chart…</p>}>
              <ForecastChart data={dayPoints} kind="day" />
            </Suspense>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Whole month: forecast vs actual</h2>
            </div>
            <Suspense fallback={<p className="muted">Loading chart…</p>}>
              <ForecastChart data={monthPoints} kind="month" />
            </Suspense>
          </section>
        </>
      )}
    </main>
  )
}
