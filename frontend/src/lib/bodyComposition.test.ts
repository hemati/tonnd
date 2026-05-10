import { describe, it, expect } from 'vitest'
import { pickComparisonMeasurement, daysBetween } from './bodyComposition'
import type { BodyMeasurement } from '../services/api'

function m(daysBack: number, fields: Partial<BodyMeasurement> = {}): BodyMeasurement {
  // Use fixed base time so day arithmetic is exact (no fractional ms issues)
  const baseTime = new Date('2026-05-10T00:00:00Z').getTime()
  const ts = baseTime - daysBack * 24 * 60 * 60 * 1000
  const d = new Date(ts)
  const iso = d.toISOString()
  return {
    date: iso.slice(0, 10),
    source: 'renpho',
    measured_at: iso,
    ...fields,
  }
}

describe('pickComparisonMeasurement', () => {
  const latest = m(0, { lean_body_mass_kg: 64.2 })

  it('picks the measurement closest to 28 days back', () => {
    const measurements = [m(35), m(28), m(21), latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked?.measured_at).toBe(measurements[1].measured_at)
  })

  it('tiebreak: equidistant measurements pick the more recent one', () => {
    // 24d and 32d are both distance 4 from the 28d marker, both within ±7d window
    const m24 = m(24)
    const m32 = m(32)
    const measurements = [m32, m24, latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked?.measured_at).toBe(m24.measured_at)
  })

  it('returns null when no measurement falls in the 21–35 day window', () => {
    // Only measurements outside ±7d of 28d
    const measurements = [m(10), m(45), latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked).toBeNull()
  })

  it('excludes the latest measurement itself from comparison', () => {
    // Only candidate is `latest` (at 0d back) which must be excluded
    const measurements = [latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked).toBeNull()
  })

  it('includes a measurement at exactly 21 days back (lower edge of window)', () => {
    const m21 = m(21)
    const measurements = [m21, latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked?.measured_at).toBe(m21.measured_at)
  })

  it('includes a measurement at exactly 35 days back (upper edge of window)', () => {
    const m35 = m(35)
    const measurements = [m35, latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked?.measured_at).toBe(m35.measured_at)
  })

  it('excludes a measurement at 20 days back (just below lower edge)', () => {
    const measurements = [m(20), latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked).toBeNull()
  })

  it('excludes a measurement at 36 days back (just above upper edge)', () => {
    const measurements = [m(36), latest]
    const picked = pickComparisonMeasurement(measurements, latest)
    expect(picked).toBeNull()
  })
})

describe('daysBetween', () => {
  it('returns positive integer days between two ISO timestamps regardless of order', () => {
    const a = '2026-01-01T08:00:00Z'
    const b = '2026-01-15T08:00:00Z'
    expect(daysBetween(a, b)).toBe(14)
    expect(daysBetween(b, a)).toBe(14)
  })

  it('rounds to the nearest day for sub-day differences', () => {
    const a = '2026-01-01T08:00:00Z'
    const b = '2026-01-08T20:00:00Z'  // 7.5 days
    expect(daysBetween(a, b)).toBe(8)
  })
})
