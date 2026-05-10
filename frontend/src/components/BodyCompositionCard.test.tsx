import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
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
})
