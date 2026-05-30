import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchUser, fetchDashboardData, syncFitbitData, initFitbitAuth,
  fetchBodyMeasurements, fetchNutritionDaily, fetchNutritionEntries,
  startFitbitBackfill, getFitbitBackfillStatus, syncOtherSources,
} from '../services/api'
import type {
  UserProfile, DashboardData, SyncResponse, FitbitInitResponse,
  BodyMeasurementsResponse, NutritionDailyResponse, NutritionEntriesResponse,
  BackfillStatus,
} from '../services/api'

// Query Keys
export const queryKeys = {
  user: ['user'] as const,
  dashboard: (days: number) => ['dashboard', days] as const,
  bodyRange: (rangeDays: number) => ['body', 'renpho', rangeDays] as const,
  bodyLatest: ['body', 'renpho', 'latest'] as const,
  nutritionDaily: (rangeDays: number) => ['nutrition', 'daily', rangeDays] as const,
  nutritionEntries: (rangeDays: number) => ['nutrition', 'entries', rangeDays] as const,
}

// =============================================================================
// User Queries
// =============================================================================

export function useUser() {
  return useQuery<UserProfile, Error>({
    queryKey: queryKeys.user,
    queryFn: fetchUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })
}

// =============================================================================
// Dashboard Queries
// =============================================================================

export function useDashboard(days: number = 30) {
  return useQuery<DashboardData, Error>({
    queryKey: queryKeys.dashboard(days),
    queryFn: () => fetchDashboardData(days),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 1,
  })
}

// =============================================================================
// Body Composition Queries (Renpho-only)
// =============================================================================

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

export function useBodyMeasurements(rangeDays: number) {
  // Buffer of 35 extra days ensures the 4-week-back comparison point is reachable
  const startDate = isoDaysAgo(rangeDays + 35)
  return useQuery<BodyMeasurementsResponse, Error>({
    queryKey: queryKeys.bodyRange(rangeDays),
    queryFn: async () => {
      // Backend returns rows in DESC order (newest first) by default.
      // Sort ASC here so consumers can rely on `data[length-1]` being the newest.
      const res = await fetchBodyMeasurements({ source: 'renpho', startDate, limit: 180 })
      return {
        count: res.count,
        data: [...res.data].sort((a, b) => a.measured_at.localeCompare(b.measured_at)),
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 3,
  })
}

export function useLatestBodyMeasurement() {
  return useQuery<BodyMeasurementsResponse, Error>({
    queryKey: queryKeys.bodyLatest,
    queryFn: () => fetchBodyMeasurements({ source: 'renpho', limit: 1 }),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 3,
  })
}

// =============================================================================
// Nutrition Queries (FatSecret)
// =============================================================================

export function useNutritionDaily(rangeDays: number) {
  // +1 to make sure today is included even when isoDaysAgo crosses a UTC boundary.
  const startDate = isoDaysAgo(rangeDays)
  return useQuery<NutritionDailyResponse, Error>({
    queryKey: queryKeys.nutritionDaily(rangeDays),
    queryFn: async () => {
      const res = await fetchNutritionDaily({ startDate, source: 'fatsecret', limit: rangeDays + 1 })
      // Backend defaults to DESC; consumers expect oldest-first for time-series charts.
      return {
        count: res.count,
        data: [...res.data].sort((a, b) => a.date.localeCompare(b.date)),
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 3,
  })
}

export function useNutritionEntries(rangeDays: number) {
  const startDate = isoDaysAgo(rangeDays)
  return useQuery<NutritionEntriesResponse, Error>({
    queryKey: queryKeys.nutritionEntries(rangeDays),
    queryFn: () => fetchNutritionEntries({ startDate, source: 'fatsecret', limit: 100 }),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 3,
  })
}

// =============================================================================
// Sync Mutations
// =============================================================================

export function useSyncFitbit() {
  const queryClient = useQueryClient()

  return useMutation<SyncResponse, Error, { days?: number; date?: string }>({
    mutationFn: syncFitbitData,
    onSuccess: () => {
      // Invalidate dashboard data to refetch after sync
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.user })
      // Invalidate body composition queries (both range-scoped and latest)
      queryClient.invalidateQueries({ queryKey: ['body'] })
      // Invalidate nutrition queries
      queryClient.invalidateQueries({ queryKey: ['nutrition'] })
    },
  })
}

const BACKFILL_ACTIVE = new Set(['pending', 'running', 'paused_rate_limited'])

export function useBackfillStatus(enabled: boolean) {
  return useQuery<BackfillStatus, Error>({
    queryKey: ['fitbit-backfill'],
    queryFn: getFitbitBackfillStatus,
    enabled,
    // Poll while the job is active; stop once done/failed/none.
    refetchInterval: (query) =>
      query.state.data && BACKFILL_ACTIVE.has(query.state.data.state) ? 4000 : false,
    staleTime: 0,
  })
}

export function useStartBackfill() {
  const queryClient = useQueryClient()
  return useMutation<BackfillStatus, Error, void>({
    mutationFn: async () => {
      const job = await startFitbitBackfill()
      // Kick off the non-Fitbit sources in parallel (single days=30 sweep).
      void syncOtherSources(30).catch(() => undefined)
      return job
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fitbit-backfill'] })
    },
  })
}

// =============================================================================
// Fitbit Auth
// =============================================================================

export function useFitbitAuth() {
  return useMutation<FitbitInitResponse, Error, void>({
    mutationFn: initFitbitAuth,
    onSuccess: (data) => {
      // Redirect to Fitbit authorization
      window.location.href = data.authorization_url
    },
  })
}
