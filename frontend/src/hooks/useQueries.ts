import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUser, fetchDashboardData, syncFitbitData, initFitbitAuth } from '../services/api'
import type { UserProfile, DashboardData, SyncResponse, FitbitInitResponse } from '../services/api'

// Query Keys
export const queryKeys = {
  user: ['user'] as const,
  dashboard: (days: number) => ['dashboard', days] as const,
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
