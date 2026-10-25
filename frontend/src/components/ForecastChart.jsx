import { useMemo } from 'react'
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const COLORS = { actual: '#14907a', forecast: '#e8743b' }
const mw = (n) => `${Math.round(n).toLocaleString('en-GB')} MW`

// Labels look like "01-06 01:00" (month) or "01:00" (day).
const FORMATS = {
  day: { tick: (l) => l, full: (l) => l },
  month: {
    tick: (l) => `${Number(l.slice(3, 5))} ${MONTHS[Number(l.slice(0, 2)) - 1]}`,
    full: (l) => `${Number(l.slice(3, 5))} ${MONTHS[Number(l.slice(0, 2)) - 1]} ${l.slice(6)}`,
  },
}

function ChartTooltip({ active, payload, format }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  const error = p.forecast - p.actual
  return (
    <div className="tooltip">
      <div className="tooltip-time">{format(p.label)}</div>
      <div><span className="dot" style={{ background: COLORS.actual }} />Actual <b>{mw(p.actual)}</b></div>
      <div><span className="dot" style={{ background: COLORS.forecast }} />Forecast <b>{mw(p.forecast)}</b></div>
      <div className="tooltip-error">Error <b>{error > 0 ? '+' : ''}{mw(error)}</b></div>
    </div>
  )
}

export default function ForecastChart({ data, kind }) {
  const format = FORMATS[kind]

  // Axis ticks are worked out once per data set, not on every redraw.
  const { xTicks, yTicks } = useMemo(() => {
    let max = 0
    for (const p of data) max = Math.max(max, p.actual, p.forecast)
    const top = Math.ceil(max / 5000) * 5000 || 5000
    const yTicks = Array.from({ length: top / 5000 + 1 }, (_, i) => i * 5000)

    const xTicks = data
      .filter((p) =>
        kind === 'day'
          ? p.label.endsWith(':00') && Number(p.label.slice(0, 2)) % 3 === 0
          : p.label.endsWith('00:00') && (Number(p.label.slice(3, 5)) - 2) % 3 === 0,
      )
      .map((p) => p.label)
    return { xTicks, yTicks }
  }, [data, kind])

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
        <defs>
          <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.actual} stopOpacity={0.28} />
            <stop offset="100%" stopColor={COLORS.actual} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="3 4" />
        <XAxis dataKey="label" ticks={xTicks} tickFormatter={format.tick} tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis ticks={yTicks} domain={[0, yTicks[yTicks.length - 1]]} tickFormatter={(v) => `${v / 1000} GW`} tickLine={false} axisLine={false} width={56} />
        <Tooltip content={<ChartTooltip format={format.full} />} cursor={{ stroke: '#8a94a3', strokeDasharray: '3 3' }} />
        <Legend verticalAlign="top" align="right" iconType="plainline" height={32} />
        <Area dataKey="actual" name="Actual" stroke={COLORS.actual} strokeWidth={2.25} fill="url(#actualFill)" dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
        <Line dataKey="forecast" name="Forecast" stroke={COLORS.forecast} strokeWidth={2.25} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
