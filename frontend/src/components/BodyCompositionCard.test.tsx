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

  it('renders error state when body query fails', async () => {
    // Body hooks set `retry: 3` per-query, which overrides QueryClient
    // defaults. Wait long enough (default backoff: 1s + 2s + 4s ≈ 7s) for the
    // final rejection to surface — `findByText` defaults to 1000ms, which is
    // not enough to cover the retry chain.
    vi.spyOn(api, 'fetchBodyMeasurements').mockRejectedValue(new Error('Network error'))
    renderCard(30)
    expect(
      await screen.findByText(/Couldn't load body composition/i, undefined, { timeout: 10000 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
  }, 15000)

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

  it('renders Renpho badge in populated state header', async () => {
    const m1 = makeMeasurement(7, { lean_body_mass_kg: 63.8, body_fat_percent: 17.0 })
    const m2 = makeMeasurement(0, { lean_body_mass_kg: 64.2, body_fat_percent: 16.6 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [m2] }
      return { count: 2, data: [m1, m2] }
    })
    renderCard(30)
    // Renpho badge appears alongside the ExpandableCard title in populated state
    const badges = await screen.findAllByText(/Renpho/i)
    expect(badges.length).toBeGreaterThan(0)
  })

  it('does not remount when the rangeDays prop changes within the same state branch (DOM root stable)', async () => {
    // NOTE: This test verifies within-state stability. Both 30D and 7D
    // mocks return populated data, so both renders hit the same render
    // branch (ExpandableCard wrapper). Cross-state stability (e.g. 30D
    // populated → 7D no-data-in-range) would require the four state
    // branches to share a common shell — currently they don't. That's
    // a larger refactor tracked as future work.
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

  it('treats the newest measurement as latest after API returns desc order', async () => {
    // Backend returns rows newest-first by default; component must sort
    // ascending so that rangeData[length-1] is actually newest.
    const newest = makeMeasurement(0, { lean_body_mass_kg: 65.0 })
    const middle = makeMeasurement(7, { lean_body_mass_kg: 64.5 })
    const oldest = makeMeasurement(14, { lean_body_mass_kg: 64.0 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [newest] }
      // Simulate backend desc order
      return { count: 3, data: [newest, middle, oldest] }
    })

    renderCard(30)
    // Preview shows newest LBM (65.0), not the desc-tail's "65.0" by coincidence.
    // Use the ExpandableCard's collapsed preview text rendering.
    expect(await screen.findByText(/65\.0 kg LBM/i)).toBeInTheDocument()
  })

  it('excludes measurements outside the selected range from displayed state', async () => {
    // Range: 30 days. Buffer: rangeDays + 35 = 65 days. Only measurement is at 45 days back.
    // The 45-day-old row should NOT make this look like "populated" — should be no-data-in-range.
    const old = makeMeasurement(45, { lean_body_mass_kg: 63.0 })
    vi.spyOn(api, 'fetchBodyMeasurements').mockImplementation(async (params) => {
      if (params.limit === 1) return { count: 1, data: [old] }
      // Buffer fetch returns the 45-day-old row (in 65-day buffer, not in 30-day window)
      return { count: 1, data: [old] }
    })

    renderCard(30)
    expect(await screen.findByText(/No measurements in last 30 days/i)).toBeInTheDocument()
  })

  it('useSyncFitbit onSuccess invalidates the body queryKey', async () => {
    // This tests the wiring in hooks/useQueries.ts. Lives here for proximity
    // to the body card's cache concerns; move to Dashboard.test.tsx once that
    // suite exists.
    const { useSyncFitbit } = await import('../hooks/useQueries')
    const { renderHook, waitFor } = await import('@testing-library/react')

    vi.spyOn(api, 'syncFitbitData').mockResolvedValue({
      success: true,
      message: 'ok',
      synced_metrics: [],
      errors: [],
    })

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const invalidateSpy = vi.spyOn(client, 'invalidateQueries')

    const { result } = renderHook(() => useSyncFitbit(), {
      wrapper: ({ children }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>,
    })

    result.current.mutate({ days: 1 })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['body'] })
  })
})
