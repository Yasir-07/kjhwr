const fmt = (n) => Math.round(n).toLocaleString('en-GB')

export default function MetricCards({ metrics }) {
  const over = metrics.bias_mw > 0
  const cards = [
    { label: 'Bias', value: `${over ? '+' : ''}${fmt(metrics.bias_mw)}`, unit: 'MW',
      hint: over ? 'Forecast too high on average' : 'Forecast too low on average', accent: true },
    { label: 'MAE', value: fmt(metrics.mae_mw), unit: 'MW', hint: 'Typical miss, ignoring direction' },
    { label: 'RMSE', value: fmt(metrics.rmse_mw), unit: 'MW', hint: 'Like MAE, big misses count extra' },
    { label: 'P90 error', value: fmt(metrics.p90_abs_error_mw), unit: 'MW', hint: '9 in 10 half-hours miss by less' },
    { label: 'MAPE', value: metrics.mape_pct.toFixed(1), unit: '%', hint: 'Miss as share of actual wind' },
  ]

  return (
    <div className="cards">
      {cards.map((c) => (
        <div className={`card${c.accent ? ' accent' : ''}`} key={c.label}>
          <div className="card-label">{c.label}</div>
          <div className="card-value">{c.value}<span className="unit">{c.unit}</span></div>
          <div className="card-hint">{c.hint}</div>
        </div>
      ))}
    </div>
  )
}
