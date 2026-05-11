import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import NutritionCard from './NutritionCard'
import * as api from '../services/api'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - days)
  return d.toISOString().slice(0, 10)
}

function makeDaily(date: string, fields: Partial<api.DailyNutrition> = {}): api.DailyNutrition {
  return { date, source: 'fatsecret', ...fields }
}

function makeEntry(date: string, fields: Partial<api.FoodEntry> = {}): api.FoodEntry {
  return {
    external_id: `ext-${date}-${Math.random()}`,
    source: 'fatsecret',
    date,
    food_entry_name: 'Test Food',
    ...fields,
  }
}

function renderCard(rangeDays: 7 | 14 | 30 = 7) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <NutritionCard rangeDays={rangeDays} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('NutritionCard', () => {
  it('renders loading state while queries pend', () => {
    vi.spyOn(api, 'fetchNutritionDaily').mockReturnValue(new Promise(() => {}))
    vi.spyOn(api, 'fetchNutritionEntries').mockReturnValue(new Promise(() => {}))
    renderCard()
    expect(screen.getByText(/Nutrition/i)).toBeInTheDocument()
    expect(screen.getByText(/Loading/i)).toBeInTheDocument()
  })

  it('renders error state with retry button when queries fail', async () => {
    // The hooks set retry: 3, so wait through the backoff (1+2+4 ≈ 7s).
    vi.spyOn(api, 'fetchNutritionDaily').mockRejectedValue(new Error('boom'))
    vi.spyOn(api, 'fetchNutritionEntries').mockRejectedValue(new Error('boom'))
    renderCard()
    expect(
      await screen.findByText(/Couldn't load nutrition data/i, undefined, { timeout: 10000 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
  }, 15000)

  it('renders no-data state when both queries return empty', async () => {
    vi.spyOn(api, 'fetchNutritionDaily').mockResolvedValue({ count: 0, data: [] })
    vi.spyOn(api, 'fetchNutritionEntries').mockResolvedValue({ count: 0, data: [] })
    renderCard()
    expect(await screen.findByText(/No food entries yet/i)).toBeInTheDocument()
    // The card mounts only for already-connected users — no Connect-FatSecret CTA here.
    expect(screen.queryByRole('link', { name: /Connect FatSecret/i })).not.toBeInTheDocument()
  })

  it('shows "No log today" preview when range has data but today is empty', async () => {
    const yesterday = isoDaysAgo(1)
    vi.spyOn(api, 'fetchNutritionDaily').mockResolvedValue({
      count: 1,
      data: [makeDaily(yesterday, { calories_in: 800, carbs_g: 80, fat_g: 30, protein_g: 50 })],
    })
    vi.spyOn(api, 'fetchNutritionEntries').mockResolvedValue({
      count: 1,
      data: [makeEntry(yesterday, { food_entry_name: 'Pasta', calories: 800 })],
    })
    renderCard()
    // Header preview shows "No log today" because no `date === today` row.
    expect(await screen.findByText(/No log today/i)).toBeInTheDocument()
  })

  it('shows today calories in the preview when today has a log', async () => {
    const today = todayISO()
    vi.spyOn(api, 'fetchNutritionDaily').mockResolvedValue({
      count: 1,
      data: [makeDaily(today, { calories_in: 1234, carbs_g: 100, fat_g: 50, protein_g: 80 })],
    })
    vi.spyOn(api, 'fetchNutritionEntries').mockResolvedValue({
      count: 1,
      data: [makeEntry(today, { food_entry_name: 'Bowl', calories: 1234 })],
    })
    renderCard()
    expect(await screen.findByText(/1,234 kcal today/i)).toBeInTheDocument()
  })

  it('renders latest meals (max 3) when expanded', async () => {
    const today = todayISO()
    const yesterday = isoDaysAgo(1)
    vi.spyOn(api, 'fetchNutritionDaily').mockResolvedValue({
      count: 2,
      data: [makeDaily(yesterday, { calories_in: 500 }), makeDaily(today, { calories_in: 600 })],
    })
    // Backend returns DESC by date — preserve that order to match production.
    vi.spyOn(api, 'fetchNutritionEntries').mockResolvedValue({
      count: 5,
      data: [
        makeEntry(today, { food_entry_name: 'Apple', calories: 95 }),
        makeEntry(today, { food_entry_name: 'Banana', calories: 105 }),
        makeEntry(today, { food_entry_name: 'Cherry', calories: 80 }),
        makeEntry(yesterday, { food_entry_name: 'Donut', calories: 250 }),
        makeEntry(yesterday, { food_entry_name: 'Eggs', calories: 150 }),
      ],
    })
    renderCard()
    // Wait for any title in the expanded card to confirm data loaded.
    expect(await screen.findByText(/600 kcal today/i)).toBeInTheDocument()
    // Click the accordion header to expand.
    fireEvent.click(screen.getByRole('button', { name: /Nutrition/i }))
    // Top 3 by date DESC = Apple/Banana/Cherry (all today).
    expect(await screen.findByText('Apple')).toBeInTheDocument()
    expect(screen.getByText('Banana')).toBeInTheDocument()
    expect(screen.getByText('Cherry')).toBeInTheDocument()
    // Donut and Eggs (yesterday) should be sliced off.
    expect(screen.queryByText('Donut')).not.toBeInTheDocument()
    expect(screen.queryByText('Eggs')).not.toBeInTheDocument()
  })

  it('renders FatSecret badge in the header', async () => {
    vi.spyOn(api, 'fetchNutritionDaily').mockResolvedValue({ count: 0, data: [] })
    vi.spyOn(api, 'fetchNutritionEntries').mockResolvedValue({ count: 0, data: [] })
    renderCard()
    expect(await screen.findByText(/FatSecret/i)).toBeInTheDocument()
  })
})
