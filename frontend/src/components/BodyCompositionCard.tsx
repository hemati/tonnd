import { ScaleIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import ExpandableCard from './ExpandableCard'
import { useBodyMeasurements, useLatestBodyMeasurement } from '../hooks/useQueries'
import { detectDataState, daysBetween, pickComparisonMeasurement, formatDelta, getDeltaColor } from '../lib/bodyComposition'
import type { DeltaField, DeltaUnit, DeltaColor } from '../lib/bodyComposition'
import type { BodyMeasurement } from '../services/api'

interface BodyCompositionCardProps {
  rangeDays: 7 | 14 | 30
}

export default function BodyCompositionCard({ rangeDays }: BodyCompositionCardProps) {
  const range = useBodyMeasurements(rangeDays)
  const latest = useLatestBodyMeasurement()

  if (range.isLoading || latest.isLoading) {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <div className="mt-4 animate-pulse text-white/40 text-sm">Loading...</div>
      </div>
    )
  }

  const rangeData = range.data?.data ?? []
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
  const lbmComparison = rangeData.length >= 2 ? pickComparisonMeasurement(rangeData, latestPoint) : null
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
      <ExpandableCard title="Body Composition" icon={ScaleIcon} preview={preview}>
        <div data-testid="chart-placeholder" className="h-[250px] bg-white/[.02] rounded" />
        <StatStrip rangeData={rangeData} />
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
      <span className="bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full text-[10px]">Renpho</span>
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

function StatStrip({ rangeData }: { rangeData: BodyMeasurement[] }) {
  const latest = rangeData[rangeData.length - 1]
  const comparison = rangeData.length >= 2 ? pickComparisonMeasurement(rangeData, latest) : null
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
