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

const FLAT_THRESHOLD = 0.1

export function formatDelta(value: number, unit: DeltaUnit): string {
  if (Math.abs(value) < FLAT_THRESHOLD) return '±0.0'
  const absValue = Math.abs(value)
  const rounded = Math.round(absValue * 10) / 10
  const sign = value > 0 ? '+' : '−' // U+2212 minus sign (typographic)
  return `${sign}${rounded.toFixed(1)} ${unit}`
}
