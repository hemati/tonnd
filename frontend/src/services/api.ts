import axios, { AxiosError } from 'axios'
import { API_URL, TOKEN_KEY } from '../config/constants'

// Axios instance with base URL
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; detail?: string }>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
    }
    const message = error.response?.data?.detail || error.response?.data?.message || error.message
    return Promise.reject(new Error(message))
  }
)

// =============================================================================
// Types
// =============================================================================

export interface UserProfile {
  user_id: string
  email: string
  fitbit_connected: boolean
  fitbit_user_id: string | null
  renpho_connected: boolean
  hevy_connected: boolean
  last_sync: string | null
}

export interface FitbitInitResponse {
  authorization_url: string
  state: string
}

export interface SyncResponse {
  success: boolean
  message: string
  synced_metrics: string[]
  errors: string[]
}

export interface WeightData {
  date: string
  weight_kg: number | null
  body_fat_percent: number | null
  bmi?: number | null
}

export interface SleepData {
  date: string
  total_minutes: number
  deep_minutes?: number
  light_minutes?: number
  rem_minutes?: number
  awake_minutes?: number
  efficiency?: number
}

export interface ActivityData {
  date: string
  steps: number
  calories_burned?: number
  distance_km?: number
  active_minutes?: number
  floors?: number
}

export interface HeartRateData {
  date: string
  resting_heart_rate?: number
  zones?: Record<string, {
    min: number
    max: number
    minutes: number
    caloriesOut: number
  }>
}

export interface HRVData {
  date: string
  daily_rmssd?: number
  deep_rmssd?: number
}

export interface SpO2Data {
  date: string
  avg?: number
  min?: number
  max?: number
}

export interface BreathingRateData {
  date: string
  breathing_rate?: number
}

export interface VO2MaxData {
  date: string
  vo2_max?: number
}

export interface TemperatureData {
  date: string
  relative_deviation?: number
}

export interface ActiveZoneMinutesData {
  date: string
  fat_burn_minutes?: number
  cardio_minutes?: number
  peak_minutes?: number
  total_minutes?: number
}

export interface WorkoutExercise {
  title: string
  volume_kg: number
  primary_muscle?: string
  secondary_muscles?: string[]
  sets: Array<{
    type: string
    weight_kg: number
    reps: number
    rpe: number | null
    distance_meters: number | null
    duration_seconds: number | null
  }>
}

export interface WorkoutData {
  date: string
  workout_count: number
  title: string
  duration_minutes: number
  total_volume_kg: number
  total_sets: number
  total_reps: number
  exercises: WorkoutExercise[]
  muscle_groups: Record<string, number>
}

export interface RecoveryData {
  date: string
  score: number
  hrv_score: number
  sleep_score: number
  rhr_score: number
}

export interface DashboardData {
  latest_weight: WeightData | null
  weight_trend: WeightData[]
  latest_sleep: SleepData | null
  sleep_history: SleepData[]
  today_activity: ActivityData | null
  activity_history: ActivityData[]
  today_heart_rate: HeartRateData | null
  latest_hrv: HRVData | null
  hrv_history: HRVData[]
  latest_spo2: SpO2Data | null
  spo2_history: SpO2Data[]
  latest_breathing_rate: BreathingRateData | null
  breathing_rate_history: BreathingRateData[]
  latest_vo2_max: VO2MaxData | null
  vo2_max_history: VO2MaxData[]
  latest_temperature: TemperatureData | null
  temperature_history: TemperatureData[]
  today_active_zone_minutes: ActiveZoneMinutesData | null
  active_zone_minutes_history: ActiveZoneMinutesData[]
  latest_workout: WorkoutData | null
  workout_history: WorkoutData[]
  recovery_score: RecoveryData | null
  recovery_history: RecoveryData[]
  last_sync: string | null
  fitbit_connected: boolean
  hevy_connected: boolean
}

// =============================================================================
// API Functions (used by React Query)
// =============================================================================

export const fetchUser = async (): Promise<UserProfile> => {
  const { data } = await api.get<UserProfile>('/api/user')
  return data
}

export const fetchDashboardData = async (days: number = 30): Promise<DashboardData> => {
  const { data } = await api.get<DashboardData>(`/api/data?days=${days}`)
  return data
}

export const initFitbitAuth = async (): Promise<FitbitInitResponse> => {
  const { data } = await api.get<FitbitInitResponse>('/auth/fitbit/init')
  return data
}

export const syncFitbitData = async (params: { days?: number; date?: string } = {}): Promise<SyncResponse> => {
  const { days = 1, date } = params
  const { data } = await api.post<SyncResponse>('/api/sync', { days, ...(date && { date }) })
  return data
}
