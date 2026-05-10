import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUser, fetchDashboardData, syncFitbitData, initFitbitAuth, fetchBodyMeasurements } from '../services/api'
import type { UserProfile, DashboardData, SyncResponse, FitbitInitResponse, BodyMeasurementsResponse } from '../services/api'

// Query Keys
export const queryKeys = {
  user: ['user'] as const,
  dashboard: (days: number) => ['dashboard', days] as const,
  bodyRange: (rangeDays: number) => ['body', 'renpho', rangeDays] as const,
  bodyLatest: ['body', 'renpho', 'latest'] as const,
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
    queryFn: () => fetchBodyMeasurements({ source: 'renpho', startDate, limit: 180 }),
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
