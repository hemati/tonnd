import type { BodyMeasurement } from '../services/api'

const DAY_MS = 24 * 60 * 60 * 1000
const TARGET_DAYS_BACK = 28
const TOLERANCE_DAYS = 7

export function pickComparisonMeasurement(
  measurements: BodyMeasurement[],
  latest: BodyMeasurement,
): BodyMeasurement | null {
  const latestMs = new Date(latest.measured_at).getTime()
  const targetMs = latestMs - TARGET_DAYS_BACK * DAY_MS
  const toleranceMs = TOLERANCE_DAYS * DAY_MS

  const candidates = measurements
    .filter((m) => m !== latest)
    .map((m) => ({
      m,
      ts: new Date(m.measured_at).getTime(),
    }))
    .filter(({ ts }) => Math.abs(ts - targetMs) <= toleranceMs)

  if (candidates.length === 0) return null

  // Sort: closer to target wins; on tie, more recent wins
  candidates.sort((a, b) => {
    const distDiff = Math.abs(a.ts - targetMs) - Math.abs(b.ts - targetMs)
    if (distDiff !== 0) return distDiff
    return b.ts - a.ts
  })

  return candidates[0].m
}

export function daysBetween(isoA: string, isoB: string): number {
  const ms = Math.abs(new Date(isoA).getTime() - new Date(isoB).getTime())
  return Math.round(ms / DAY_MS)
}

export type DeltaUnit = 'kg' | 'pp' | 'pts'
export type DeltaField = 'lbm' | 'fat_mass' | 'body_fat_pct' | 'muscle_mass_pct' | 'water_pct' | 'visceral_fat'
export type DeltaColor = 'cyan' | 'warning' | 'neutral'

const FLAT_THRESHOLD = 0.1

const GOOD_DIRECTION: Record<DeltaField, 'up' | 'down' | null> = {
  lbm: 'up',
  fat_mass: 'down',
  body_fat_pct: 'down',
  muscle_mass_pct: 'up',
  water_pct: null,        // informational, no goal direction
  visceral_fat: 'down',
}

export function formatDelta(value: number, unit: DeltaUnit): string {
  if (Math.abs(value) < FLAT_THRESHOLD) return '±0.0'
  const absValue = Math.abs(value)
  const rounded = Math.round(absValue * 10) / 10
  const sign = value > 0 ? '+' : '−' // U+2212 minus sign (typographic)
  return `${sign}${rounded.toFixed(1)} ${unit}`
}

export function getDeltaColor(field: DeltaField, value: number): DeltaColor {
  if (Math.abs(value) < FLAT_THRESHOLD) return 'neutral'
  const direction = GOOD_DIRECTION[field]
  if (direction === null) return 'neutral'
  const actual = value > 0 ? 'up' : 'down'
  return actual === direction ? 'cyan' : 'warning'
}

export type DataState = 'no-data-ever' | 'no-data-in-range' | 'single-point' | 'full'

export function detectDataState(
  rangeMeasurements: BodyMeasurement[],
  latestMeasurements: BodyMeasurement[],
): DataState {
  if (rangeMeasurements.length === 0 && latestMeasurements.length === 0) return 'no-data-ever'
  if (rangeMeasurements.length === 0) return 'no-data-in-range'
  if (rangeMeasurements.length === 1) return 'single-point'
  return 'full'
}
