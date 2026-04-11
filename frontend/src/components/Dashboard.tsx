import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { trackEvent } from '../lib/analytics'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, Legend, ComposedChart,
} from 'recharts'
import {
  ScaleIcon, MoonIcon, HeartIcon, ArrowPathIcon, BoltIcon,
  ChartBarIcon, ExclamationCircleIcon, FireIcon, CloudIcon,
  SunIcon, BoltSlashIcon, ArrowTrendingUpIcon, ChartBarSquareIcon,
  EllipsisHorizontalCircleIcon,
} from '@heroicons/react/24/outline'
import { cn } from '../lib/utils'
import { useDashboard, useUser, useSyncFitbit } from '../hooks/useQueries'

// Heroicons type
type HeroIcon = React.ForwardRefExoticComponent<React.PropsWithoutRef<React.SVGProps<SVGSVGElement>> & { title?: string; titleId?: string } & React.RefAttributes<SVGSVGElement>>

// Color palette — monochrome with subtle accents
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

// Tooltip style for recharts
const tooltipStyle = {
  contentStyle: { backgroundColor: '#141414', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px' },
  labelStyle: { color: '#e5e5e5' },
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [daysToShow, setDaysToShow] = useState(7)
  const [syncProgress, setSyncProgress] = useState<string | null>(null)

  const { data: user } = useUser()
  const { data, isLoading, error, refetch } = useDashboard(30)
  const syncMutation = useSyncFitbit()

  // Redirect if no data source connected
  useEffect(() => {
    if (user && !user.fitbit_connected && !user.renpho_connected) {
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

  const formatLastSync = (lastSync: string | null) => {
    if (!lastSync) return 'Never'
    try { return format(parseISO(lastSync), 'MMM d, yyyy h:mm a') } catch { return lastSync }
  }

  const getFilteredData = <T,>(arr: T[] | undefined): T[] => arr?.slice(0, daysToShow) ?? []

  // Calculate stats
  const weeklySummary = data?.activity_history ? (() => {
    const recent = getFilteredData(data.activity_history)
    if (!recent.length) return null
    const totalSteps = recent.reduce((s, d) => s + (d.steps || 0), 0)
    const totalCalories = recent.reduce((s, d) => s + (d.calories_burned || 0), 0)
    const totalActiveMinutes = recent.reduce((s, d) => s + (d.active_minutes || 0), 0)
    const sleepDays = getFilteredData(data.sleep_history)
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
        <button onClick={() => refetch()} className="bg-white text-black hover:bg-white/90 px-4 py-2 rounded-lg">
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Health Dashboard</h1>
          <p className="text-white/40 text-sm">Last synced: {formatLastSync(data?.last_sync || null)}</p>
          {syncProgress && <p className="text-white/80 text-sm animate-pulse">{syncProgress}</p>}
        </div>
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

      {/* Weekly Summary */}
      {weeklySummary && (
        <div className="rounded-xl p-6 border border-white/[.06] bg-white/[.02]">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <ChartBarSquareIcon className="h-5 w-5" /> {daysToShow}-Day Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
            <div><p className="text-2xl font-bold text-white/80">{weeklySummary.totalSteps.toLocaleString()}</p><p className="text-white/40 text-sm">Total Steps</p></div>
            <div><p className="text-2xl font-bold text-white/70">{weeklySummary.avgSteps.toLocaleString()}</p><p className="text-white/40 text-sm">Avg Steps/Day</p></div>
            <div><p className="text-2xl font-bold text-white/70">{weeklySummary.totalCalories.toLocaleString()}</p><p className="text-white/40 text-sm">Total Calories</p></div>
            <div><p className="text-2xl font-bold text-white/60">{weeklySummary.avgCalories.toLocaleString()}</p><p className="text-white/40 text-sm">Avg Cal/Day</p></div>
            <div><p className="text-2xl font-bold text-white/60">{weeklySummary.totalActiveMinutes}</p><p className="text-white/40 text-sm">Active Min</p></div>
            <div><p className="text-2xl font-bold text-white/80">{Math.floor(weeklySummary.avgSleep / 60)}h {weeklySummary.avgSleep % 60}m</p><p className="text-white/40 text-sm">Avg Sleep</p></div>
          </div>
        </div>
      )}

      {/* Today's Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={ScaleIcon} iconBg="bg-white/[.06]" title="Weight"
          value={data?.latest_weight?.weight_kg ? `${Number(data.latest_weight.weight_kg).toFixed(1)} kg` : '--'}
          subtitle={data?.latest_weight?.body_fat_percent ? `Body Fat: ${Number(data.latest_weight.body_fat_percent).toFixed(1)}%` : undefined} />
        <StatCard icon={MoonIcon} iconBg="bg-white/[.06]" title="Last Night Sleep"
          value={data?.latest_sleep?.total_minutes ? `${Math.floor(data.latest_sleep.total_minutes / 60)}h ${data.latest_sleep.total_minutes % 60}m` : '--'}
          subtitle={data?.latest_sleep?.efficiency ? `Efficiency: ${data.latest_sleep.efficiency}%` : undefined} />
        <StatCard icon={ChartBarIcon} iconBg="bg-white/[.06]" title="Steps Today"
          value={data?.today_activity?.steps?.toLocaleString() || '--'}
          subtitle={data?.today_activity?.distance_km ? `Distance: ${Number(data.today_activity.distance_km).toFixed(1)} km` : undefined} />
        <StatCard icon={HeartIcon} iconBg="bg-white/[.06]" title="Resting Heart Rate"
          value={data?.today_heart_rate?.resting_heart_rate ? `${data.today_heart_rate.resting_heart_rate} bpm` : '--'}
          subtitle={data?.today_activity?.calories_burned ? `Calories: ${data.today_activity.calories_burned.toLocaleString()}` : undefined} />
      </div>

      {/* Health Vitals Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recovery Score */}
        <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><BoltSlashIcon className="h-5 w-5" /> Recovery Score</h2>
          {data?.recovery_score ? (
            <div className="text-center">
              <div className={cn('inline-flex items-center justify-center w-24 h-24 rounded-full text-3xl font-bold',
                data.recovery_score.score >= 75 ? 'bg-white/[.06] text-white/70' :
                data.recovery_score.score >= 50 ? 'bg-white/[.06] text-white/50' : 'bg-white/[.06] text-white/60')}>
                {data.recovery_score.score}
              </div>
              <p className="text-white/40 text-sm mt-3">
                {data.recovery_score.score >= 75 ? '✨ Ready for high intensity' :
                 data.recovery_score.score >= 50 ? '⚡ Light activity recommended' : '💤 Focus on recovery'}
              </p>
            </div>
          ) : <p className="text-white/40 text-center">No data</p>}
        </div>

        {/* Health Vitals */}
        <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
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
        <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><ArrowTrendingUpIcon className="h-5 w-5" /> Cardio Fitness</h2>
          {data?.latest_vo2_max?.vo2_max ? (() => {
            const v = Number(data.latest_vo2_max.vo2_max)
            return (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-white/[.06]">
                  <span className="text-3xl font-bold text-white/80">{v.toFixed(0)}</span>
                </div>
                <p className="text-white/50 mt-2">VO₂ Max <span className="text-white/30 text-sm">ml/kg/min</span></p>
                <div className="mt-4 bg-white/[.04] rounded-lg p-3">
                  <p className={cn('font-semibold', v >= 50 ? 'text-white/80' : v >= 40 ? 'text-white/60' : v >= 30 ? 'text-white/50' : 'text-white/40')}>
                    {v >= 50 ? 'Excellent' : v >= 40 ? 'Good' : v >= 30 ? 'Fair' : 'Needs Improvement'}
                  </p>
                </div>
              </div>
            )
          })() : <p className="text-white/40 text-center">No data</p>}
        </div>
      </div>

      {/* Active Zone Minutes */}
      {data?.today_active_zone_minutes && (
        <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><BoltIcon className="h-5 w-5" /> Active Zone Minutes (Today)</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className="bg-white/[.03] rounded-lg p-4">
              <p className="text-3xl font-bold text-white/80">{data.today_active_zone_minutes.total_minutes || 0}</p>
              <p className="text-white/40 text-sm">Total</p>
            </div>
            <div className="bg-white/[.03] rounded-lg p-4 border border-white/[.06]">
              <p className="text-2xl font-bold text-white/70">{data.today_active_zone_minutes.fat_burn_minutes || 0}</p>
              <p className="text-white/40 text-sm">Fat Burn</p>
            </div>
            <div className="bg-white/[.03] rounded-lg p-4 border border-white/[.06]">
              <p className="text-2xl font-bold text-white/50">{data.today_active_zone_minutes.cardio_minutes || 0}</p>
              <p className="text-white/40 text-sm">Cardio</p>
            </div>
            <div className="bg-white/[.03] rounded-lg p-4 border border-white/[.06]">
              <p className="text-2xl font-bold text-white/60">{data.today_active_zone_minutes.peak_minutes || 0}</p>
              <p className="text-white/40 text-sm">Peak</p>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      {data?.activity_history && data.activity_history.length > 0 && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Steps Trend" icon={ChartBarIcon}>
              <ResponsiveContainer width="100%" height={256}>
                <BarChart data={prepareChartData(getFilteredData(data.activity_history))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                  <Tooltip {...tooltipStyle} formatter={(v: any) => [v.toLocaleString(), 'Steps']} />
                  <Bar dataKey="steps" fill={COLORS.success} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Calories Burned" icon={FireIcon}>
              <ResponsiveContainer width="100%" height={256}>
                <AreaChart data={prepareChartData(getFilteredData(data.activity_history))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip {...tooltipStyle} formatter={(v: any) => [v.toLocaleString(), 'Calories']} />
                  <Area type="monotone" dataKey="calories_burned" stroke={COLORS.warning} fill={COLORS.warning} fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* HRV & Recovery */}
          {data.hrv_history?.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartCard title="HRV Trend" icon={HeartIcon}>
                <ResponsiveContainer width="100%" height={256}>
                  <LineChart data={prepareChartData(getFilteredData(data.hrv_history).filter(d => d.daily_rmssd))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} domain={['dataMin - 5', 'dataMax + 5']} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${v.toFixed(1)} ms`, 'HRV']} />
                    <Line type="monotone" dataKey="daily_rmssd" stroke={COLORS.purple} strokeWidth={2} dot={{ fill: COLORS.purple, r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              {data.recovery_history?.length > 0 && (
                <ChartCard title="Recovery Score Trend" icon={BoltSlashIcon}>
                  <ResponsiveContainer width="100%" height={256}>
                    <AreaChart data={prepareChartData(getFilteredData(data.recovery_history))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} />
                      <Tooltip {...tooltipStyle} formatter={(v: any) => [v, 'Score']} />
                      <Area type="monotone" dataKey="score" stroke={COLORS.success} fill={COLORS.success} fillOpacity={0.3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </ChartCard>
              )}
            </div>
          )}

          {/* Sleep Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {data.sleep_history?.length > 0 && (
              <ChartCard title="Sleep Duration" icon={MoonIcon}>
                <ResponsiveContainer width="100%" height={256}>
                  <ComposedChart data={prepareChartData(getFilteredData(data.sleep_history)).map(d => ({ ...d, hours: Number((d.total_minutes / 60).toFixed(1)) }))} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={v => `${v}h`} domain={[0, 12]} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${v} hours`, 'Sleep']} />
                    <Bar dataKey="hours" fill={COLORS.purple} radius={[4, 4, 0, 0]} />
                    <Line type="monotone" dataKey={() => 8} stroke="#22c55e" strokeDasharray="5 5" dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </ChartCard>
            )}

            {sleepBreakdown && sleepBreakdown.length > 0 && (
              <ChartCard title="Last Night Sleep Stages" icon={MoonIcon}>
                <ResponsiveContainer width="100%" height={256}>
                  <PieChart>
                    <Pie data={sleepBreakdown} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={3} dataKey="value">
                      {sleepBreakdown.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${Math.floor(v / 60)}h ${v % 60}m`, '']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            )}
          </div>

          {/* Heart Rate & Weight */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {heartRateZones && heartRateZones.length > 0 && (
              <ChartCard title="Heart Rate Zones (Today)" icon={HeartIcon}>
                <ResponsiveContainer width="100%" height={256}>
                  <BarChart data={heartRateZones} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={11} tickFormatter={v => `${v}m`} />
                    <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={75} />
                    <Tooltip {...tooltipStyle} formatter={(v: any) => [`${v} min`, 'Time']} />
                    <Bar dataKey="minutes" radius={[0, 4, 4, 0]}>
                      {heartRateZones.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            )}

            {data.weight_trend?.length > 0 && (
              <ChartCard title="Weight Trend" icon={ScaleIcon}>
                <ResponsiveContainer width="100%" height={256}>
                  <LineChart data={prepareChartData(getFilteredData(data.weight_trend).filter(d => d.weight_kg))} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} domain={['dataMin - 1', 'dataMax + 1']} tickFormatter={v => `${v}kg`} />
                    <Tooltip {...tooltipStyle} />
                    <Line type="monotone" dataKey="weight_kg" name="Weight" stroke={COLORS.cyan} strokeWidth={2} dot={{ fill: COLORS.cyan }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            )}
          </div>
        </>
      )}

      {/* No Data */}
      {!data?.latest_weight && !data?.latest_sleep && !data?.today_activity && (
        <div className="bg-white/[.02] rounded-xl p-8 border border-white/[.06] text-center">
          <ChartBarSquareIcon className="h-16 w-16 text-white/40 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Data Yet</h2>
          <p className="text-white/40 mb-4">Click "Sync Now" to fetch your Fitbit data</p>
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
// Helper Components
// =============================================================================

function StatCard({ icon: Icon, iconBg, title, value, subtitle }: {
  icon: HeroIcon, iconBg: string, title: string, value: string, subtitle?: string
}) {
  return (
    <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
      <div className="flex items-center gap-3 mb-4">
        <div className={cn('w-10 h-10 rounded-full flex items-center justify-center', iconBg)}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-white/40 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
      {subtitle && <p className="text-white/40 text-sm">{subtitle}</p>}
    </div>
  )
}

function VitalRow({ icon: Icon, label, value, color }: {
  icon: HeroIcon, label: string, value: string, color: string
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

function ChartCard({ title, icon: Icon, children }: {
  title: string, icon: HeroIcon, children: React.ReactNode
}) {
  return (
    <div className="bg-white/[.02] rounded-xl p-6 border border-white/[.06]">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Icon className="h-5 w-5" /> {title}
      </h2>
      {children}
    </div>
  )
}

function prepareChartData<T extends { date: string }>(data: T[]): (T & { date: string })[] {
  return [...data].reverse().map(d => ({ ...d, date: format(parseISO(d.date), 'MMM d') }))
}
