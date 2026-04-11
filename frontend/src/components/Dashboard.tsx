import { useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, parseISO, differenceInHours } from 'date-fns'
import { trackEvent } from '../lib/analytics'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, Legend, ComposedChart,
  ReferenceLine,
} from 'recharts'
import {
  ScaleIcon, MoonIcon, HeartIcon, ArrowPathIcon, BoltIcon,
  ChartBarIcon, ExclamationCircleIcon, FireIcon, CloudIcon,
  SunIcon, BoltSlashIcon, ArrowTrendingUpIcon, ChartBarSquareIcon,
  EllipsisHorizontalCircleIcon, ChevronDownIcon, ChevronUpIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../lib/utils'
import { useDashboard, useUser, useSyncFitbit } from '../hooks/useQueries'
import MuscleMap from './MuscleMap'

// Heroicons type
type HeroIcon = React.ForwardRefExoticComponent<React.PropsWithoutRef<React.SVGProps<SVGSVGElement>> & { title?: string; titleId?: string } & React.RefAttributes<SVGSVGElement>>

// =============================================================================
// Design Tokens
// =============================================================================

const COLORS = {
  primary: '#ffffff',
  success: '#4ade80',
  warning: '#fbbf24',
  danger: '#f87171',
  purple: '#a78bfa',
  pink: '#f472b6',
  cyan: '#67e8f9',
  slate: '#6b7280',
}

const SLEEP_COLORS = { deep: '#818cf8', light: '#a78bfa', rem: '#c084fc', awake: '#6b7280' }
const HR_ZONE_COLORS: Record<string, string> = {
  'Out of Range': '#6b7280', 'Fat Burn': '#4ade80', 'Cardio': '#fbbf24', 'Peak': '#f87171',
}

const tooltipStyle = {
  contentStyle: { backgroundColor: '#141414', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px' },
  labelStyle: { color: '#e5e5e5' },
}

const CARD = 'bg-white/[.02] rounded-xl border border-white/[.06]'

// =============================================================================
// Utility Functions
// =============================================================================

function prepareChartData<T extends { date: string }>(data: T[]): (T & { date: string })[] {
  return [...data].reverse().map(d => ({ ...d, date: format(parseISO(d.date), 'MMM d') }))
}

/** Exponentially Weighted Moving Average */
function ewma(values: number[], span: number = 7): number[] {
  const alpha = 2 / (span + 1)
  const result: number[] = []
  let prev = values[0]
  for (const v of values) {
    prev = alpha * v + (1 - alpha) * prev
    result.push(Math.round(prev * 10) / 10)
  }
  return result
}

/** Pearson correlation coefficient */
function pearsonR(x: number[], y: number[]): number | null {
  const n = Math.min(x.length, y.length)
  if (n < 5) return null
  const xs = x.slice(0, n), ys = y.slice(0, n)
  const mx = xs.reduce((a, b) => a + b, 0) / n
  const my = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, dx2 = 0, dy2 = 0
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - mx, dy = ys[i] - my
    num += dx * dy; dx2 += dx * dx; dy2 += dy * dy
  }
  const denom = Math.sqrt(dx2 * dy2)
  return denom === 0 ? null : Math.round((num / denom) * 100) / 100
}

/** Staleness level from a date string */
function staleness(dateStr: string | null | undefined): 'fresh' | 'aging' | 'stale' | 'very-stale' | 'none' {
  if (!dateStr) return 'none'
  try {
    const hours = differenceInHours(new Date(), parseISO(dateStr))
    if (hours < 6) return 'fresh'
    if (hours < 48) return 'aging'
    if (hours < 168) return 'stale'
    return 'very-stale'
  } catch { return 'none' }
}

function recoveryColor(score: number) {
  if (score >= 85) return COLORS.success
  if (score >= 70) return COLORS.warning
  return COLORS.danger
}

// =============================================================================
// Dashboard
// =============================================================================

export default function Dashboard() {
  const navigate = useNavigate()
  const [daysToShow, setDaysToShow] = useState(7)
  const [syncProgress, setSyncProgress] = useState<string | null>(null)

  const { data: user } = useUser()
  const { data, isLoading, error, refetch } = useDashboard(30)
  const syncMutation = useSyncFitbit()

  useEffect(() => {
    if (user && !user.fitbit_connected && !user.renpho_connected && !user.hevy_connected) {
      navigate('/sources')
    }
  }, [user, navigate])

  const handleSync = () => {
    trackEvent('manual_sync')
    syncMutation.mutate({ days: 1 })
  }

  const handleHistoricalSync = async () => {
    if (!confirm('Sync last 30 days? This will be done in 10 batches.')) return
    for (let i = 0; i < 10; i++) {
      setSyncProgress(`Syncing batch ${i + 1}/10...`)
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - (i * 3))
      await syncMutation.mutateAsync({ days: 3, date: startDate.toISOString().split('T')[0] })
      if (i < 9) await new Promise(r => setTimeout(r, 1000))
    }
    setSyncProgress(null)
    refetch()
  }

  const formatLastSync = (ls: string | null) => {
    if (!ls) return 'Never'
    try { return format(parseISO(ls), 'MMM d, yyyy h:mm a') } catch { return ls }
  }

  const getFiltered = <T,>(arr: T[] | undefined): T[] => arr?.slice(0, daysToShow) ?? []

  // Computed values
  const weeklySummary = data?.activity_history ? (() => {
    const recent = getFiltered(data.activity_history)
    if (!recent.length) return null
    const totalSteps = recent.reduce((s, d) => s + (d.steps || 0), 0)
    const totalCalories = recent.reduce((s, d) => s + (d.calories_burned || 0), 0)
    const totalActiveMinutes = recent.reduce((s, d) => s + (d.active_minutes || 0), 0)
    const sleepDays = getFiltered(data.sleep_history)
    const avgSleep = sleepDays.length ? Math.round(sleepDays.reduce((s, d) => s + (d.total_minutes || 0), 0) / sleepDays.length) : 0
    return {
      totalSteps, totalCalories, totalActiveMinutes,
      avgSteps: Math.round(totalSteps / recent.length),
      avgCalories: Math.round(totalCalories / recent.length),
      avgSleep, daysTracked: recent.length,
    }
  })() : null

  const sleepBreakdown = data?.latest_sleep ? [
    { name: 'Deep', value: data.latest_sleep.deep_minutes || 0, color: SLEEP_COLORS.deep },
    { name: 'Light', value: data.latest_sleep.light_minutes || 0, color: SLEEP_COLORS.light },
    { name: 'REM', value: data.latest_sleep.rem_minutes || 0, color: SLEEP_COLORS.rem },
    { name: 'Awake', value: data.latest_sleep.awake_minutes || 0, color: SLEEP_COLORS.awake },
  ].filter(i => i.value > 0) : null

  const heartRateZones = data?.today_heart_rate?.zones
    ? Object.entries(data.today_heart_rate.zones).map(([name, z]) => ({
        name, minutes: z.minutes, color: HR_ZONE_COLORS[name] || COLORS.slate,
      })).filter(z => z.minutes > 0)
    : null

  // Recovery score — backend returns a plain number, components computed locally
  const recoveryScoreValue = typeof data?.recovery_score === 'number'
    ? data.recovery_score
    : (data?.recovery_score as any)?.score ?? null

  const recoveryComponents = recoveryScoreValue !== null ? {
    score: recoveryScoreValue as number,
    hrv: Math.round(Math.min(100, (Number(data?.latest_hrv?.daily_rmssd ?? 0) / 100) * 100)),
    sleep: data?.latest_sleep?.efficiency ?? 0,
    rhr: Math.round(Math.max(0, Math.min(100, (100 - Number(data?.today_heart_rate?.resting_heart_rate ?? 70)) * 2))),
  } : null

  // EWMA weight data
  const weightWithEwma = (() => {
    const raw = getFiltered(data?.weight_trend)?.filter(d => d.weight_kg)
    if (!raw || raw.length < 2) return null
    const reversed = [...raw].reverse()
    const weights = reversed.map(d => Number(d.weight_kg))
    const smoothed = ewma(weights)
    return reversed.map((d, i) => ({
      date: format(parseISO(d.date), 'MMM d'),
      raw: Number(d.weight_kg),
      trend: smoothed[i],
      body_fat: d.body_fat_percent ? Number(d.body_fat_percent) : undefined,
    }))
  })()

  // Sleep-HRV correlation data
  const sleepHrvCorrelation = (() => {
    const sleep = getFiltered(data?.sleep_history)
    const hrv = getFiltered(data?.hrv_history)
    if (!sleep?.length || !hrv?.length) return null

    const hrvByDate = new Map(hrv.map(h => [h.date, h.daily_rmssd]))
    const paired = sleep
      .filter(s => s.efficiency && hrvByDate.has(s.date))
      .map(s => ({
        date: format(parseISO(s.date), 'MMM d'),
        sleepEfficiency: s.efficiency!,
        hrv: Number(hrvByDate.get(s.date)!),
      }))
      .reverse()

    if (paired.length < 3) return null
    const r = pearsonR(paired.map(p => p.sleepEfficiency), paired.map(p => p.hrv))
    return { data: paired, r }
  })()

  const syncStaleness = staleness(data?.last_sync)

  // Loading / Error states
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-12 w-12 animate-spin text-white/50" />
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="h-16 w-16 text-white/50 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Error Loading Data</h2>
        <p className="text-white/40 mb-4">{error.message}</p>
        <button onClick={() => refetch()} className="bg-white text-black hover:bg-white/90 px-4 py-2 rounded-lg">Try Again</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Health Dashboard</h1>
          <p className="text-white/40 text-sm flex items-center gap-2">
            Last synced: {formatLastSync(data?.last_sync || null)}
            <StaleBadge level={syncStaleness} />
          </p>
          {syncProgress && <p className="text-white/80 text-sm animate-pulse">{syncProgress}</p>}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleHistoricalSync} disabled={syncMutation.isPending}
            className="bg-white/[.08] hover:bg-white/[.12] disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm">
            Sync 30 Days
          </button>
          <button onClick={handleSync} disabled={syncMutation.isPending}
            className="bg-white text-black hover:bg-white/90 disabled:opacity-50 px-4 py-2 rounded-lg flex items-center gap-2">
            <ArrowPathIcon className={cn('h-4 w-4', syncMutation.isPending && 'animate-spin')} />
            {syncMutation.isPending ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════
          CURRENT — latest values, no time period toggle
          ════════════════════════════════════════════════════════════ */}

      {/* ── Recovery Score ──────────────────────────────────────── */}
      <div className={cn(CARD, 'p-6')}>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BoltSlashIcon className="h-5 w-5" /> Recovery Score
        </h2>
        {recoveryComponents ? (
          <div className="flex items-center gap-8">
            <div className="text-center flex-shrink-0">
              <p className="text-5xl font-bold" style={{ color: recoveryColor(recoveryComponents.score) }}>
                {recoveryComponents.score}
              </p>
              <p className="text-white/40 text-xs mt-1">
                {recoveryComponents.score >= 85 ? 'High intensity' :
                 recoveryComponents.score >= 75 ? 'Moderate' :
                 recoveryComponents.score >= 50 ? 'Light activity' : 'Recovery day'}
              </p>
            </div>
            <div className="space-y-3 flex-1 min-w-0">
              <FactorBar label="HRV" value={recoveryComponents.hrv} />
              <FactorBar label="Sleep" value={recoveryComponents.sleep} />
              <FactorBar label="Resting HR" value={recoveryComponents.rhr} />
            </div>
          </div>
        ) : (
          <p className="text-white/40 text-center py-4">Need HRV, sleep, and heart rate data</p>
        )}
      </div>

      {/* ── Stat Cards (latest values) ─────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard icon={ScaleIcon} title="Weight"
          value={data?.latest_weight?.weight_kg ? `${Number(data.latest_weight.weight_kg).toFixed(1)} kg` : '--'}
          subtitle={data?.latest_weight?.body_fat_percent ? `Body Fat: ${Number(data.latest_weight.body_fat_percent).toFixed(1)}%` : undefined}
          staleLevel={staleness(data?.latest_weight?.date)} />
        <StatCard icon={MoonIcon} title="Last Night Sleep"
          value={data?.latest_sleep?.total_minutes ? `${Math.floor(data.latest_sleep.total_minutes / 60)}h ${data.latest_sleep.total_minutes % 60}m` : '--'}
          subtitle={data?.latest_sleep?.efficiency ? `Efficiency: ${data.latest_sleep.efficiency}%` : undefined}
          staleLevel={staleness(data?.latest_sleep?.date)} />
        <StatCard icon={ChartBarIcon} title="Steps Today"
          value={data?.today_activity?.steps?.toLocaleString() || '--'}
          subtitle={data?.today_activity?.distance_km ? `Distance: ${Number(data.today_activity.distance_km).toFixed(1)} km` : undefined}
          staleLevel={staleness(data?.today_activity?.date)} />
        <StatCard icon={HeartIcon} title="Resting Heart Rate"
          value={data?.today_heart_rate?.resting_heart_rate ? `${data.today_heart_rate.resting_heart_rate} bpm` : '--'}
          subtitle={data?.today_activity?.calories_burned ? `Calories: ${data.today_activity.calories_burned.toLocaleString()}` : undefined}
          staleLevel={staleness(data?.today_heart_rate?.date)} />
        <StatCard icon={BoltIcon} title="Last Workout"
          value={data?.latest_workout?.title || '--'}
          subtitle={data?.latest_workout ? `${Math.round(data.latest_workout.total_volume_kg).toLocaleString()}kg · ${data.latest_workout.duration_minutes}min · ${data.latest_workout.total_sets} sets` : undefined}
          staleLevel={staleness(data?.latest_workout?.date)} />
      </div>

      {/* ── Bento Grid: Health Vitals Row ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Vitals */}
        <div className={cn(CARD, 'p-6')}>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><FireIcon className="h-5 w-5" /> Health Vitals</h2>
          <div className="space-y-4">
            <VitalRow icon={EllipsisHorizontalCircleIcon} label="Blood Oxygen" value={data?.latest_spo2?.avg ? `${Number(data.latest_spo2.avg).toFixed(1)}%` : '--'}
              color={Number(data?.latest_spo2?.avg ?? 0) >= 95 ? 'text-white/70' : 'text-white/50'} />
            <VitalRow icon={CloudIcon} label="Breathing Rate" value={data?.latest_breathing_rate?.breathing_rate ? `${Number(data.latest_breathing_rate.breathing_rate).toFixed(1)}/min` : '--'} color="text-white/80" />
            <VitalRow icon={SunIcon} label="Skin Temp" value={data?.latest_temperature?.relative_deviation !== undefined
              ? `${Number(data.latest_temperature.relative_deviation) > 0 ? '+' : ''}${Number(data.latest_temperature.relative_deviation).toFixed(1)}°C` : '--'}
              color={Math.abs(Number(data?.latest_temperature?.relative_deviation ?? 0)) <= 0.5 ? 'text-white/70' : 'text-white/50'} />
            <VitalRow icon={HeartIcon} label="HRV (RMSSD)" value={data?.latest_hrv?.daily_rmssd ? `${Number(data.latest_hrv.daily_rmssd).toFixed(0)} ms` : '--'} color="text-white/60" />
          </div>
        </div>

        {/* VO2 Max */}
        <div className={cn(CARD, 'p-6')}>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><ArrowTrendingUpIcon className="h-5 w-5" /> Cardio Fitness</h2>
          {data?.latest_vo2_max?.vo2_max ? (() => {
            const v = Number(data.latest_vo2_max.vo2_max)
            return (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/[.06]">
                  <span className="text-3xl font-bold text-white/80">{v.toFixed(0)}</span>
                </div>
                <p className="text-white/50 mt-2">VO₂ Max <span className="text-white/30 text-sm">ml/kg/min</span></p>
                <div className="mt-3 bg-white/[.04] rounded-lg p-2">
                  <p className={cn('font-semibold text-sm', v >= 50 ? 'text-white/80' : v >= 40 ? 'text-white/60' : 'text-white/50')}>
                    {v >= 50 ? 'Excellent' : v >= 40 ? 'Good' : v >= 30 ? 'Fair' : 'Needs Improvement'}
                  </p>
                </div>
              </div>
            )
          })() : <p className="text-white/40 text-center">No data</p>}
        </div>

        {/* Active Zone Minutes */}
        {data?.today_active_zone_minutes && (
          <div className={cn(CARD, 'p-6')}>
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><BoltIcon className="h-5 w-5" /> Active Zone Min</h2>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-white/[.03] rounded-lg p-3">
                <p className="text-2xl font-bold text-white/80">{data.today_active_zone_minutes.total_minutes || 0}</p>
                <p className="text-white/40 text-xs">Total</p>
              </div>
              <div className="bg-white/[.03] rounded-lg p-3">
                <p className="text-xl font-bold text-white/70">{data.today_active_zone_minutes.fat_burn_minutes || 0}</p>
                <p className="text-white/40 text-xs">Fat Burn</p>
              </div>
              <div className="bg-white/[.03] rounded-lg p-3">
                <p className="text-xl font-bold text-white/50">{data.today_active_zone_minutes.cardio_minutes || 0}</p>
                <p className="text-white/40 text-xs">Cardio</p>
              </div>
              <div className="bg-white/[.03] rounded-lg p-3">
                <p className="text-xl font-bold text-white/60">{data.today_active_zone_minutes.peak_minutes || 0}</p>
                <p className="text-white/40 text-xs">Peak</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ════════════════════════════════════════════════════════════
          TRENDS — time-period-dependent charts
          ════════════════════════════════════════════════════════════ */}

      {data?.activity_history && data.activity_history.length > 0 && (
        <>
          {/* ── Trends Header with Toggle + Period Summary ────── */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-white/[.06]">
            <h2 className="text-xl font-semibold text-white">Trends</h2>
            <div className="flex items-center gap-3">
              <div className="flex bg-white/[.04] rounded-lg p-1">
                {[7, 14, 30].map(d => (
                  <button key={d} onClick={() => setDaysToShow(d)}
                    className={cn('px-3 py-1 text-sm rounded-md transition-colors',
                      daysToShow === d ? 'bg-white/[.15] text-white' : 'text-white/40 hover:text-white')}>
                    {d}D
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Period Summary */}
          {weeklySummary && (
            <div className={cn(CARD, 'p-6')}>
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <ChartBarSquareIcon className="h-5 w-5" /> {daysToShow}-Day Summary
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
                <SummaryCell value={weeklySummary.totalSteps.toLocaleString()} label="Total Steps" />
                <SummaryCell value={weeklySummary.avgSteps.toLocaleString()} label="Avg Steps/Day" />
                <SummaryCell value={weeklySummary.totalCalories.toLocaleString()} label="Total Calories" />
                <SummaryCell value={weeklySummary.avgCalories.toLocaleString()} label="Avg Cal/Day" />
                <SummaryCell value={String(weeklySummary.totalActiveMinutes)} label="Active Min" />
                <SummaryCell value={`${Math.floor(weeklySummary.avgSleep / 60)}h ${weeklySummary.avgSleep % 60}m`} label="Avg Sleep" />
              </div>
            </div>
          )}

          {/* Steps + Calories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ExpandableCard title="Steps Trend" icon={ChartBarIcon}
              preview={<span className="text-white/60 text-sm">{weeklySummary?.avgSteps.toLocaleString()} avg/day</span>}>
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={prepareChartData(getFiltered(data.activity_history))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                  <YAxis stroke="#9CA3AF" fontSize={11} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                  <Tooltip {...tooltipStyle} formatter={(v: any) => [v.toLocaleString(), 'Steps']} />
                  <Bar dataKey="steps" fill={COLORS.success} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ExpandableCard>

            <ExpandableCard title="Calories Burned" icon={FireIcon}
              preview={<span className="text-white/60 text-sm">{weeklySummary?.avgCalories.toLocaleString()} avg/day</span>}>
              <ResponsiveContainer width="100%" height={256}>
                <AreaChart data={prepareChartData(getFiltered(data.activity_history))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                  <YAxis stroke="#9CA3AF" fontSize={11} />
                  <Tooltip {...tooltipStyle} formatter={(v: any) => [v.toLocaleString(), 'Calories']} />
                  <Area type="monotone" dataKey="calories_burned" stroke={COLORS.warning} fill={COLORS.warning} fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </ExpandableCard>
          </div>

          {/* HRV + Sleep-HRV Correlation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.hrv_history?.length > 0 && (
              <ExpandableCard title="HRV Trend" icon={HeartIcon}
                preview={data.latest_hrv?.daily_rmssd
                  ? <span className="text-white/60 text-sm">{Number(data.latest_hrv.daily_rmssd).toFixed(0)} ms</span>
                  : undefined}>
                <ResponsiveContainer width="100%" height={256}>
                  <LineChart data={prepareChartData(getFiltered(data.hrv_history).filter(d => d.daily_rmssd))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                    <YAxis stroke="#9CA3AF" fontSize={11} domain={['dataMin - 5', 'dataMax + 5']} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${Number(v).toFixed(1)} ms`, 'HRV']} />
                    <Line type="monotone" dataKey="daily_rmssd" stroke={COLORS.purple} strokeWidth={2} dot={{ fill: COLORS.purple, r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}

            {/* US 6: Sleep-HRV Correlation */}
            {sleepHrvCorrelation && (
              <ExpandableCard title="Sleep ↔ HRV Correlation" icon={MoonIcon}
                preview={sleepHrvCorrelation.r !== null
                  ? <span className="text-white/60 text-sm">r = {sleepHrvCorrelation.r.toFixed(2)}</span>
                  : undefined}>
                <div>
                  {sleepHrvCorrelation.r !== null && (
                    <p className="text-white/40 text-xs mb-3">
                      Pearson r = {sleepHrvCorrelation.r.toFixed(2)} — {
                        Math.abs(sleepHrvCorrelation.r) >= 0.7 ? 'Strong' :
                        Math.abs(sleepHrvCorrelation.r) >= 0.4 ? 'Moderate' : 'Weak'
                      } correlation ({sleepHrvCorrelation.data.length} days)
                    </p>
                  )}
                  <ResponsiveContainer width="100%" height={240}>
                    <ComposedChart data={sleepHrvCorrelation.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                      <YAxis yAxisId="sleep" stroke="#9CA3AF" fontSize={11} domain={[60, 100]} tickFormatter={v => `${v}%`} />
                      <YAxis yAxisId="hrv" orientation="right" stroke="#9CA3AF" fontSize={11} domain={['dataMin - 5', 'dataMax + 5']} />
                      <Tooltip {...tooltipStyle} />
                      <Bar yAxisId="sleep" dataKey="sleepEfficiency" name="Sleep Eff %" fill={SLEEP_COLORS.deep} fillOpacity={0.4} radius={[3, 3, 0, 0]} />
                      <Line yAxisId="hrv" type="monotone" dataKey="hrv" name="HRV (ms)" stroke={COLORS.purple} strokeWidth={2} dot={{ fill: COLORS.purple, r: 3 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </ExpandableCard>
            )}
          </div>

          {/* Sleep Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.sleep_history?.length > 0 && (
              <ExpandableCard title="Sleep Duration" icon={MoonIcon}
                preview={data.latest_sleep ? <span className="text-white/60 text-sm">{Math.floor(data.latest_sleep.total_minutes / 60)}h {data.latest_sleep.total_minutes % 60}m last night</span> : undefined}>
                <ResponsiveContainer width="100%" height={256}>
                  <ComposedChart data={prepareChartData(getFiltered(data.sleep_history)).map(d => ({ ...d, hours: Number((d.total_minutes / 60).toFixed(1)) }))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                    <YAxis stroke="#9CA3AF" fontSize={11} tickFormatter={v => `${v}h`} domain={[0, 12]} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${v} hours`, 'Sleep']} />
                    <Bar dataKey="hours" fill={COLORS.purple} radius={[4, 4, 0, 0]} />
                    <ReferenceLine y={8} stroke="#22c55e" strokeDasharray="5 5" label={{ value: '8h goal', fill: '#22c55e', fontSize: 10, position: 'right' }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}

            {sleepBreakdown && sleepBreakdown.length > 0 && (
              <ExpandableCard title="Last Night Sleep Stages" icon={MoonIcon}
                preview={<span className="text-white/60 text-sm">{sleepBreakdown.find(s => s.name === 'Deep')?.value ?? 0}m deep</span>}>
                <ResponsiveContainer width="100%" height={256}>
                  <PieChart>
                    <Pie data={sleepBreakdown} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={3} dataKey="value">
                      {sleepBreakdown.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${Math.floor(v / 60)}h ${v % 60}m`, '']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}
          </div>

          {/* Heart Rate + Weight */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {heartRateZones && heartRateZones.length > 0 && (
              <ExpandableCard title="Heart Rate Zones (Today)" icon={HeartIcon}
                preview={<span className="text-white/60 text-sm">{data.today_heart_rate?.resting_heart_rate} bpm resting</span>}>
                <ResponsiveContainer width="100%" height={256}>
                  <BarChart data={heartRateZones} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" stroke="#9CA3AF" fontSize={11} tickFormatter={v => `${v}m`} />
                    <YAxis type="category" dataKey="name" stroke="#9CA3AF" fontSize={11} width={75} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${v} min`, 'Time']} />
                    <Bar dataKey="minutes" radius={[0, 4, 4, 0]}>
                      {heartRateZones.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}

            {/* US 3: Weight with EWMA */}
            {weightWithEwma && weightWithEwma.length > 0 && (
              <ExpandableCard title="Weight Trend" icon={ScaleIcon}
                preview={<span className="text-white/60 text-sm">{weightWithEwma[weightWithEwma.length - 1].trend} kg trend</span>}>
                <ResponsiveContainer width="100%" height={256}>
                  <ComposedChart data={weightWithEwma} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
                    <YAxis yAxisId="weight" stroke="#9CA3AF" fontSize={11} domain={['dataMin - 1', 'dataMax + 1']} tickFormatter={v => `${v}kg`} />
                    {weightWithEwma.some(d => d.body_fat !== undefined) && (
                      <YAxis yAxisId="fat" orientation="right" stroke="#9CA3AF" fontSize={11} tickFormatter={v => `${v}%`} />
                    )}
                    <Tooltip {...tooltipStyle} />
                    <Line yAxisId="weight" type="monotone" dataKey="raw" name="Daily" stroke={COLORS.cyan} strokeWidth={1} strokeDasharray="3 3" dot={{ fill: COLORS.cyan, r: 2 }} />
                    <Line yAxisId="weight" type="monotone" dataKey="trend" name="Trend (EWMA)" stroke={COLORS.cyan} strokeWidth={2.5} dot={false} />
                    {weightWithEwma.some(d => d.body_fat !== undefined && d.body_fat > 0) && (
                      <Line yAxisId="fat" type="monotone" dataKey="body_fat" name="Body Fat %" stroke={COLORS.warning} strokeWidth={1.5} dot={{ fill: COLORS.warning, r: 2 }} />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}
          </div>
        </>
      )}

      {/* ── Workout Section ────────────────────────────────────── */}
      {data?.workout_history && data.workout_history.length > 0 && (() => {
        const workouts = data.workout_history
        const aggregatedMuscles: Record<string, number> = {}
        const exercisesByGroup: Record<string, string[]> = {}

        for (const w of workouts) {
          if (w.muscle_groups) {
            for (const [group, sets] of Object.entries(w.muscle_groups)) {
              aggregatedMuscles[group] = (aggregatedMuscles[group] || 0) + sets
            }
          }
          for (const ex of w.exercises || []) {
            const groups = new Set<string>()
            if (ex.primary_muscle) groups.add(ex.primary_muscle)
            for (const sec of ex.secondary_muscles || []) groups.add(sec)
            if (groups.size === 0) groups.add('other')
            for (const group of groups) {
              if (!exercisesByGroup[group]) exercisesByGroup[group] = []
              if (!exercisesByGroup[group].includes(ex.title)) {
                exercisesByGroup[group].push(ex.title)
              }
            }
          }
        }

        const volumeData = prepareChartData(workouts.map(w => ({
          date: w.date,
          volume: Math.round(w.total_volume_kg),
          title: w.title,
          duration: w.duration_minutes,
        })))

        const lastWorkout = workouts[0]
        const exerciseData = lastWorkout?.exercises
          ?.map(e => ({ name: e.title, volume: Math.round(e.volume_kg) }))
          .sort((a, b) => b.volume - a.volume)
          .slice(0, 8) || []



        return (
          <>
            {/* Muscle Heatmap */}
            <div className={cn(CARD, 'p-6')}>
              <h2 className="text-lg font-semibold text-white mb-4">Muscle Heatmap</h2>
              <MuscleMap muscleGroups={aggregatedMuscles} exercisesByGroup={exercisesByGroup} />
            </div>

            {/* Volume Trend */}
            <ExpandableCard title="Volume Trend" icon={ArrowTrendingUpIcon}
              preview={`${workouts.length} workouts · avg ${Math.round(workouts.reduce((s, w) => s + w.total_volume_kg, 0) / workouts.length).toLocaleString()}kg`}>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={volumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <Tooltip {...tooltipStyle}
                    formatter={(v) => [`${Number(v).toLocaleString()} kg`, 'Volume']}
                    labelFormatter={(l, payload) => {
                      const item = payload?.[0]?.payload
                      return item ? `${l} · ${item.title} · ${item.duration}min` : l
                    }} />
                  <Bar dataKey="volume" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ExpandableCard>

            {/* Exercise Breakdown */}
            {exerciseData.length > 0 && (
              <ExpandableCard title="Exercise Breakdown" icon={ChartBarIcon}
                preview={`${lastWorkout.title} · ${exerciseData.length} exercises`}>
                <ResponsiveContainer width="100%" height={Math.max(200, exerciseData.length * 36)}>
                  <BarChart data={exerciseData} layout="vertical" margin={{ left: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" tick={{ fill: '#e5e5e5', fontSize: 11 }} width={80} />
                    <Tooltip {...tooltipStyle} formatter={(v) => [`${Number(v).toLocaleString()} kg`, 'Volume']} />
                    <Bar dataKey="volume" fill="#a78bfa" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ExpandableCard>
            )}
          </>
        )
      })()}

      {/* No Data */}
      {!data?.latest_weight && !data?.latest_sleep && !data?.today_activity && !data?.latest_workout && (
        <div className={cn(CARD, 'p-8 text-center')}>
          <ChartBarSquareIcon className="h-16 w-16 text-white/40 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Data Yet</h2>
          <p className="text-white/40 mb-4">Click "Sync Now" to fetch your health data</p>
          <button onClick={handleSync} disabled={syncMutation.isPending}
            className="bg-white text-black hover:bg-white/90 disabled:opacity-50 px-6 py-2 rounded-lg">
            {syncMutation.isPending ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Sub-components
// =============================================================================

/** US 4: Staleness indicator */
function StaleBadge({ level }: { level: ReturnType<typeof staleness> }) {
  if (level === 'none') return null
  const styles = {
    'fresh': 'bg-green-500',
    'aging': 'bg-amber-500',
    'stale': 'bg-amber-600',
    'very-stale': 'bg-red-500',
  }
  return <span className={cn('inline-block w-2 h-2 rounded-full', styles[level])} />
}

/** US 2: Factor progress bar for recovery breakdown */
function FactorBar({ label, value }: { label: string; value: number }) {
  // Semantic dot color: green ≥70, amber 40-69, red <40
  const dotColor = value >= 70 ? COLORS.success : value >= 40 ? COLORS.warning : COLORS.danger

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-white/50 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dotColor }} />
          {label}
        </span>
        <span className="text-white/40">{value}%</span>
      </div>
      <div className="h-1.5 bg-white/[.06] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${Math.min(100, value)}%`,
            background: 'linear-gradient(90deg, rgba(34,211,238,0.4), rgba(34,211,238,0.8))',
          }}
        />
      </div>
    </div>
  )
}

function SummaryCell({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="text-2xl font-bold text-white/80">{value}</p>
      <p className="text-white/40 text-sm">{label}</p>
    </div>
  )
}

/** US 4: Stat card with staleness indicator */
function StatCard({ icon: Icon, title, value, subtitle, staleLevel }: {
  icon: HeroIcon; title: string; value: string; subtitle?: string; staleLevel?: ReturnType<typeof staleness>
}) {
  return (
    <div className={cn(CARD, 'p-6', staleLevel === 'stale' && 'opacity-60', staleLevel === 'very-stale' && 'opacity-40')}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-white/[.06] flex items-center justify-center">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="text-white/40 text-sm">{title}</p>
            {staleLevel && <StaleBadge level={staleLevel} />}
          </div>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
      {subtitle && <p className="text-white/40 text-sm">{subtitle}</p>}
    </div>
  )
}

function VitalRow({ icon: Icon, label, value, color }: {
  icon: HeroIcon; label: string; value: string; color: string
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-white/40" />
        <span className="text-white/50">{label}</span>
      </div>
      <span className={cn('text-lg font-semibold', color)}>{value}</span>
    </div>
  )
}

/** US 5: Expandable card with progressive disclosure */
function ExpandableCard({ title, icon: Icon, preview, children, className }: {
  title: string; icon: HeroIcon; preview?: ReactNode; children: ReactNode; className?: string
}) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className={cn(CARD, 'overflow-hidden', className)}>
      <button onClick={() => setExpanded(!expanded)}
        className="w-full p-6 flex items-center justify-between text-left hover:bg-white/[.01] transition-colors">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-white/60" />
          <h2 className="text-lg font-semibold text-white">{title}</h2>
        </div>
        <div className="flex items-center gap-3">
          {!expanded && preview}
          {expanded
            ? <ChevronUpIcon className="h-4 w-4 text-white/30" />
            : <ChevronDownIcon className="h-4 w-4 text-white/30" />}
        </div>
      </button>
      <div className={cn('transition-all duration-300 ease-in-out', expanded ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden')}>
        <div className="px-6 pb-6">
          {children}
        </div>
      </div>
    </div>
  )
}
