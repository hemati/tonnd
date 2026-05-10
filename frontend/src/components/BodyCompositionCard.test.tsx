import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import BodyCompositionCard from './BodyCompositionCard'
import * as api from '../services/api'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString()
}

function makeMeasurement(daysAgo: number, fields: Partial<api.BodyMeasurement> = {}): api.BodyMeasurement {
  const measured = isoDaysAgo(daysAgo)
  return {
    date: measured.slice(0, 10),
    source: 'renpho',
    measured_at: measured,
    ...fields,
  }
}

function renderCard(rangeDays: 7 | 14 | 30 = 30) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <BodyCompositionCard rangeDays={rangeDays} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('BodyCompositionCard', () => {
  it('renders the card title and a loading indicator while queries pend', () => {
    // Never-resolving promise pins the queries in `isLoading` so we hit the
    // loading branch deterministically — independent of later state branches.
    vi.spyOn(api, 'fetchBodyMeasurements').mockReturnValue(new Promise(() => {}))
    renderCard()
    expect(screen.getByText(/Body Composition/i)).toBeInTheDocument()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('renders empty state with Renpho CTA when no data exists for any source', async () => {
    vi.spyOn(api, 'fetchBodyMeasurements').mockResolvedValue({ count: 0, data: [] })
    renderCard()
    expect(await screen.findByText(/Renpho needed for muscle mass and lean body mass tracking/i)).toBeInTheDocument()
    const cta = screen.getByRole('link', { name: /Connect Renpho/i })
    expect(cta).toHaveAttribute('href', '/sources#renpho')
  })

  it('renders "no measurements in last N days" when range is empty but latest has data', async () => {
    const latestMeasurement = makeMeasurement(45, { lean_body_mass_kg: 64.2 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      // limit: 1 → latest probe; otherwise → range query
      if (params.limit === 1) return { count: 1, data: [latestMeasurement] }
      return { count: 0, data: [] }
    })
    renderCard(30)
    expect(await screen.findByText(/No measurements in last 30 days/i)).toBeInTheDocument()
    expect(screen.getByText(/Last measurement was 45 days ago/i)).toBeInTheDocument()
  })

  it('renders stat strip with the four fields in correct order', async () => {
    const latestMeasurement = makeMeasurement(0, {
      lean_body_mass_kg: 64.2,
      body_fat_percent: 16.6,
      muscle_mass_percent: 42.1,
      body_water_percent: 58.4,
      visceral_fat: 4.2,
    })
    const olderMeasurement = makeMeasurement(7, {
      lean_body_mass_kg: 63.8,
      body_fat_percent: 17.0,
      muscle_mass_percent: 41.8,
      body_water_percent: 58.5,
      visceral_fat: 4.4,
    })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [latestMeasurement] }
      return { count: 2, data: [olderMeasurement, latestMeasurement] }
    })

    renderCard(30)
    // All four stat labels should appear in order
    const labels = await screen.findAllByTestId('stat-label')
    expect(labels.map((el) => el.textContent)).toEqual(['Body Fat %', 'Muscle Mass %', 'Water %', 'Visceral Fat'])
    // Current values
    expect(screen.getByTestId('stat-value-body_fat_pct')).toHaveTextContent('16.6')
    expect(screen.getByTestId('stat-value-muscle_mass_pct')).toHaveTextContent('42.1')
    expect(screen.getByTestId('stat-value-water_pct')).toHaveTextContent('58.4')
    expect(screen.getByTestId('stat-value-visceral_fat')).toHaveTextContent('4.2')
  })

  it('renders chart with LBM and Fat Mass lines when data has 2+ points', async () => {
    const m1 = makeMeasurement(14, { lean_body_mass_kg: 63.5, body_fat_percent: 17.2, weight_kg: 76.6 })
    const m2 = makeMeasurement(7, { lean_body_mass_kg: 63.8, body_fat_percent: 17.0, weight_kg: 76.9 })
    const m3 = makeMeasurement(0, { lean_body_mass_kg: 64.2, body_fat_percent: 16.6, weight_kg: 77.0 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [m3] }
      return { count: 3, data: [m1, m2, m3] }
    })

    renderCard(30)
    expect(await screen.findByTestId('body-chart')).toBeInTheDocument()
  })

  it('weight toggle reveals the dotted weight line on click', async () => {
    const m1 = makeMeasurement(14, { lean_body_mass_kg: 63.5, weight_kg: 76.6, body_fat_percent: 17 })
    const m2 = makeMeasurement(0, { lean_body_mass_kg: 64.2, weight_kg: 77.0, body_fat_percent: 16.6 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [m2] }
      return { count: 2, data: [m1, m2] }
    })
    renderCard(30)
    // Test against aria-pressed (locale-independent + a11y signal),
    // not the visible text label which may be localized later.
    const toggle = await screen.findByTestId('weight-toggle')
    expect(toggle).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-pressed', 'true')
  })

  it('does not remount when the rangeDays prop changes (DOM root stable)', async () => {
    const m30 = makeMeasurement(15, { lean_body_mass_kg: 63.5, body_fat_percent: 17 })
    const mLatest = makeMeasurement(0, { lean_body_mass_kg: 64.2, body_fat_percent: 16.6 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [mLatest] }
      return { count: 2, data: [m30, mLatest] }
    })

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    function Wrapper({ days }: { days: 7 | 14 | 30 }) {
      return (
        <QueryClientProvider client={client}>
          <MemoryRouter>
            <BodyCompositionCard rangeDays={days} />
          </MemoryRouter>
        </QueryClientProvider>
      )
    }

    const { rerender, findByTestId } = render(<Wrapper days={30} />)
    const rootBefore = await findByTestId('body-card-root')
    rerender(<Wrapper days={7} />)
    const rootAfter = await findByTestId('body-card-root')
    expect(rootAfter).toBe(rootBefore)
  })
})
