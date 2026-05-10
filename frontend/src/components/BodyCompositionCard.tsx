import { useState } from 'react'
import { ScaleIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { ComposedChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import ExpandableCard from './ExpandableCard'
import { useBodyMeasurements, useLatestBodyMeasurement } from '../hooks/useQueries'
import { detectDataState, daysBetween, pickComparisonMeasurement, formatDelta, getDeltaColor, filterToRange } from '../lib/bodyComposition'
import type { DeltaField, DeltaUnit, DeltaColor } from '../lib/bodyComposition'
import type { BodyMeasurement } from '../services/api'

interface BodyCompositionCardProps {
  rangeDays: 7 | 14 | 30
}

export default function BodyCompositionCard({ rangeDays }: BodyCompositionCardProps) {
  const range = useBodyMeasurements(rangeDays)
  const latest = useLatestBodyMeasurement()
  const [showWeight, setShowWeight] = useState(false)

  if (range.isLoading || latest.isLoading) {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <div className="mt-4 animate-pulse text-white/40 text-sm">Loading...</div>
      </div>
    )
  }

  // Error branch — render before state detection so API failures are not
  // misclassified as "no data" (which would show the Renpho CTA instead).
  if (range.isError || latest.isError) {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <ErrorState onRetry={() => { range.refetch(); latest.refetch() }} />
      </div>
    )
  }

  // The hook fetches `rangeDays + 35` days to keep the 4-week comparison point
  // in scope. `comparisonPool` includes that buffer; `rangeData` is filtered to
  // the user-visible window for chart, state detection, and current-value display.
  const comparisonPool = range.data?.data ?? []
  const rangeData = filterToRange(comparisonPool, rangeDays)
  const latestData = latest.data?.data ?? []
  const state = detectDataState(rangeData, latestData)

  if (state === 'no-data-ever') {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <NoDataEver />
      </div>
    )
  }

  if (state === 'no-data-in-range') {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <NoDataInRange rangeDays={rangeDays} latest={latestData[0]} />
      </div>
    )
  }

  // Populated states (single-point or full): use ExpandableCard
  const latestPoint = rangeData[rangeData.length - 1]
  const lbm = latestPoint.lean_body_mass_kg
  // Δ uses the buffered comparisonPool so the 4-week-back point is reachable
  // even when the user-selected window is shorter than 28 days.
  const lbmComparison = comparisonPool.length >= 2 ? pickComparisonMeasurement(comparisonPool, latestPoint) : null
  const lbmDelta = lbm !== undefined && lbmComparison?.lean_body_mass_kg !== undefined
    ? lbm - lbmComparison.lean_body_mass_kg
    : null

  const preview = (
    <span className="text-white/60 text-sm">
      {lbm !== undefined ? `${lbm.toFixed(1)} kg LBM` : '—'}
      {lbmDelta !== null && ` · ${formatDelta(lbmDelta, 'kg')}`}
    </span>
  )

  return (
    <div data-testid="body-card-root">
      <ExpandableCard title="Body Composition" icon={ScaleIcon} preview={preview} headerExtra={<RenphoBadge />}>
        <div className="flex justify-end">
          <button
            type="button"
            data-testid="weight-toggle"
            aria-pressed={showWeight}
            onClick={() => setShowWeight((v) => !v)}
            className="text-xs text-white/50 hover:text-white/80"
          >
            {showWeight ? 'Hide weight' : 'Show weight'}
          </button>
        </div>
        <BodyChart rangeData={rangeData} showWeight={showWeight} isSinglePoint={state === 'single-point'} />
        <StatStrip rangeData={rangeData} comparisonPool={comparisonPool} />
      </ExpandableCard>
    </div>
  )
}

// Used by loading + empty-state shells (which don't use ExpandableCard,
// so they need their own header rendering).
function EmptyHeader({ rangeDays }: { rangeDays: number }) {
  return (
    <div className="flex justify-between items-start">
      <div>
        <h3 className="text-white font-semibold text-base">Body Composition</h3>
        <p className="text-white/40 text-xs mt-1">{rangeDays}-day trend</p>
      </div>
      <RenphoBadge />
    </div>
  )
}

function RenphoBadge() {
  return (
    <span className="bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full text-[10px]">Renpho</span>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">Couldn't load body composition.</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 px-4 py-2 bg-white/[.06] hover:bg-white/[.10] text-white text-sm rounded-lg"
      >
        Retry
      </button>
    </div>
  )
}

function NoDataEver() {
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">Renpho needed for muscle mass and lean body mass tracking</p>
      <Link
        to="/sources#renpho"
        className="inline-block mt-4 px-4 py-2 bg-cyan-500/10 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/20"
      >
        Connect Renpho
      </Link>
    </div>
  )
}

function NoDataInRange({ rangeDays, latest }: { rangeDays: number; latest: BodyMeasurement }) {
  const daysSince = daysBetween(latest.measured_at, new Date().toISOString())
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">No measurements in last {rangeDays} days.</p>
      <p className="text-white/40 text-xs mt-1">Last measurement was {daysSince} days ago.</p>
    </div>
  )
}

type NumericKey<T> = { [K in keyof T]-?: T[K] extends number | undefined ? K : never }[keyof T]

const STAT_FIELDS: Array<{
  key: DeltaField
  label: string
  measurementKey: NumericKey<BodyMeasurement>
  unit: DeltaUnit
  format: (v: number) => string
}> = [
  { key: 'body_fat_pct', label: 'Body Fat %', measurementKey: 'body_fat_percent', unit: 'pp', format: (v) => `${v.toFixed(1)} %` },
  { key: 'muscle_mass_pct', label: 'Muscle Mass %', measurementKey: 'muscle_mass_percent', unit: 'pp', format: (v) => `${v.toFixed(1)} %` },
  { key: 'water_pct', label: 'Water %', measurementKey: 'body_water_percent', unit: 'pp', format: (v) => `${v.toFixed(1)} %` },
  { key: 'visceral_fat', label: 'Visceral Fat', measurementKey: 'visceral_fat', unit: 'pts', format: (v) => v.toFixed(1) },
]

const COLOR_CLASS: Record<DeltaColor, string> = {
  cyan: 'text-cyan-400',
  warning: 'text-amber-500',
  neutral: 'text-white/40',
}

const CELL_TOOLTIPS: Partial<Record<DeltaField, string>> = {
  water_pct: 'Used for measurement quality, not a goal metric',
  visceral_fat: 'Visceral fat rating, lower is better',
}

interface StatCellProps {
  field: DeltaField
  label: string
  currentValue: number | undefined
  delta: number | null
  unit: DeltaUnit
  format: (v: number) => string
  daysBack: number | null
}

function StatCell({ field, label, currentValue, delta, unit, format, daysBack }: StatCellProps) {
  const tooltip = CELL_TOOLTIPS[field]
  return (
    <div className="rounded-lg bg-white/[.02] border border-white/[.06] p-3" title={tooltip}>
      <div data-testid="stat-label" className="text-[10px] uppercase tracking-wider text-white/50">{label}</div>
      <div data-testid={`stat-value-${field}`} className="text-2xl font-semibold text-white">
        {currentValue !== undefined ? format(currentValue) : '—'}
      </div>
      <div
        data-testid={`stat-delta-${field}`}
        className={`text-[11px] mt-1 ${delta === null ? 'text-white/40' : COLOR_CLASS[getDeltaColor(field, delta)]}`}
        title={delta !== null && daysBack !== null ? `vs. ${daysBack} days ago` : undefined}
      >
        {delta === null ? '—' : formatDelta(delta, unit)}
      </div>
    </div>
  )
}

function StatStrip({ rangeData, comparisonPool }: { rangeData: BodyMeasurement[]; comparisonPool: BodyMeasurement[] }) {
  const latest = rangeData[rangeData.length - 1]
  // Use the buffered comparisonPool (rangeDays + 35 days) so the 4-week-back
  // point can be picked even on short ranges.
  const comparison = comparisonPool.length >= 2 ? pickComparisonMeasurement(comparisonPool, latest) : null
  const daysBack = comparison ? daysBetween(comparison.measured_at, latest.measured_at) : null

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
      {STAT_FIELDS.map((cfg) => {
        const cur = latest[cfg.measurementKey]
        const prev = comparison ? comparison[cfg.measurementKey] : undefined
        const delta = cur !== undefined && prev !== undefined ? cur - prev : null
        return (
          <StatCell
            key={cfg.key}
            field={cfg.key}
            label={cfg.label}
            currentValue={cur}
            delta={delta}
            unit={cfg.unit}
            format={cfg.format}
            daysBack={daysBack}
          />
        )
      })}
    </div>
  )
}

function deriveFatMassKg(m: BodyMeasurement): number | undefined {
  if (m.weight_kg !== undefined && m.body_fat_percent !== undefined) {
    return +(m.weight_kg * (m.body_fat_percent / 100)).toFixed(2)
  }
  return undefined
}

function buildChartData(rangeData: BodyMeasurement[]) {
  return rangeData.map((m) => ({
    date: m.date,
    lbm: m.lean_body_mass_kg,
    fat_mass: deriveFatMassKg(m),
    weight: m.weight_kg,
  }))
}

interface BodyChartProps {
  rangeData: BodyMeasurement[]
  showWeight: boolean
  isSinglePoint: boolean
}

function BodyChart({ rangeData, showWeight, isSinglePoint }: BodyChartProps) {
  const chartData = buildChartData(rangeData)
  return (
    <div data-testid="body-chart" className="mt-4">
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
          <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
          <YAxis yAxisId="lbm" stroke="#9CA3AF" fontSize={11} domain={['dataMin - 1', 'dataMax + 1']} tickFormatter={(v) => `${v}kg`} />
          <YAxis yAxisId="fat" orientation="right" stroke="#9CA3AF" fontSize={11} domain={['dataMin - 1', 'dataMax + 1']} tickFormatter={(v) => `${v}kg`} />
          <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,.1)' }} />
          <Line yAxisId="lbm" type="monotone" dataKey="lbm" name="LBM" stroke="#22d3ee" strokeWidth={2.5} dot={{ fill: '#22d3ee', r: 3 }} />
          <Line yAxisId="fat" type="monotone" dataKey="fat_mass" name="Fat Mass" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 3 }} />
          {showWeight && (
            <Line yAxisId="lbm" type="monotone" dataKey="weight" name="Weight" stroke="rgba(255,255,255,0.3)" strokeWidth={1.5} strokeDasharray="4 3" dot={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
      {isSinglePoint && (
        <p className="text-center text-white/40 text-xs mt-2">Take more measurements to see trends</p>
      )}
    </div>
  )
}
