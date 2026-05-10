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
})
