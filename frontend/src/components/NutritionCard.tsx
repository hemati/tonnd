import { useMemo, type ReactNode } from 'react'
import { FireIcon } from '@heroicons/react/24/outline'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from 'recharts'
import ExpandableCard from './ExpandableCard'
import { CARD } from '../lib/cardStyles'
import { useNutritionDaily, useNutritionEntries } from '../hooks/useQueries'
import type { DailyNutrition, FoodEntry } from '../services/api'

interface NutritionCardProps {
  rangeDays: 7 | 14 | 30
}

const MACRO_COLORS = {
  carbs: '#fbbf24',
  fat: '#f472b6',
  protein: '#22d3ee',
  fiber: '#a3e635',
}

const MEAL_LABELS: Record<string, string> = {
  breakfast: 'Breakfast',
  lunch: 'Lunch',
  dinner: 'Dinner',
  other: 'Snack',
  snack: 'Snack',
}

export default function NutritionCard({ rangeDays }: NutritionCardProps) {
  const daily = useNutritionDaily(rangeDays)
  const entries = useNutritionEntries(rangeDays)

  const dailyData = useMemo(() => daily.data?.data ?? [], [daily.data])
  const entryData = useMemo(() => entries.data?.data ?? [], [entries.data])

  // Filter to user-visible window. Hook fetches rangeDays + 1 to handle UTC boundary.
  const windowedDaily = useMemo(() => filterToRangeDaily(dailyData, rangeDays), [dailyData, rangeDays])

  // "Today" means actual today (UTC), not "newest row in range" — yesterday's
  // 800 kcal must not appear under "Today" if today has no log yet.
  const todayISO = new Date().toISOString().slice(0, 10)
  const today = windowedDaily.find((d) => d.date === todayISO) ?? null
  const todayEntryCount = entryData.filter((e) => e.date === todayISO).length

  // Backend returns entries in DESC order (newest first); take the head directly.
  const latestMeals = useMemo(() => entryData.slice(0, 3), [entryData])

  if (daily.isLoading || entries.isLoading) {
    return (
      <NonExpandableShell rangeDays={rangeDays}>
        <div className="mt-4 animate-pulse text-white/40 text-sm">Loading...</div>
      </NonExpandableShell>
    )
  }

  if (daily.isError || entries.isError) {
    return (
      <NonExpandableShell rangeDays={rangeDays}>
        <ErrorState onRetry={() => { daily.refetch(); entries.refetch() }} />
      </NonExpandableShell>
    )
  }

  const hasAnyData = windowedDaily.length > 0 || entryData.length > 0

  if (!hasAnyData) {
    return (
      <NonExpandableShell rangeDays={rangeDays}>
        <NoDataEver />
      </NonExpandableShell>
    )
  }

  const todayCalories = today?.calories_in ?? 0
  const preview = (
    <span className="text-white/60 text-sm">
      {todayCalories > 0 ? `${Math.round(todayCalories).toLocaleString()} kcal today` : 'No log today'}
    </span>
  )

  return (
    <div data-testid="nutrition-card-root">
      <ExpandableCard title="Nutrition" icon={FireIcon} preview={preview} headerExtra={<FatSecretBadge />}>
        <TodayMacroSummary today={today} entryCount={todayEntryCount} />
        <CaloriesChart data={windowedDaily} />
        <MacrosChart data={windowedDaily} />
        <LatestMealsList meals={latestMeals} />
      </ExpandableCard>
    </div>
  )
}

function NonExpandableShell({ rangeDays, children }: { rangeDays: number; children: ReactNode }) {
  return (
    <div data-testid="nutrition-card-root" className={`${CARD} p-5`}>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-white font-semibold text-base">Nutrition</h3>
          <p className="text-white/40 text-xs mt-1">{rangeDays}-day intake</p>
        </div>
        <FatSecretBadge />
      </div>
      {children}
    </div>
  )
}

function FatSecretBadge() {
  return (
    <span className="bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full text-[10px]">FatSecret</span>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">Couldn't load nutrition data.</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 px-4 py-2 bg-white/[.06] hover:bg-white/[.10] text-white text-sm rounded-lg"
      >
        Retry
      </button>
    </div>
  )
}

function NoDataEver() {
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">No food entries yet. Log a meal in the FatSecret app — it'll appear after the next sync.</p>
    </div>
  )
}

function TodayMacroSummary({ today, entryCount }: { today: DailyNutrition | null; entryCount: number }) {
  const macros = useMemo(() => {
    if (!today) return []
    return [
      { name: 'Carbs', value: today.carbs_g ?? 0, color: MACRO_COLORS.carbs },
      { name: 'Fat', value: today.fat_g ?? 0, color: MACRO_COLORS.fat },
      { name: 'Protein', value: today.protein_g ?? 0, color: MACRO_COLORS.protein },
    ].filter((m) => m.value > 0)
  }, [today])

  if (!today || macros.length === 0) {
    return (
      <div className="rounded-lg bg-white/[.02] border border-white/[.06] p-4 text-center text-white/40 text-sm">
        No meals logged today
      </div>
    )
  }

  const totalGrams = macros.reduce((s, m) => s + m.value, 0)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
      <div className="sm:col-span-1 rounded-lg bg-white/[.02] border border-white/[.06] p-3">
        <div className="text-[10px] uppercase tracking-wider text-white/50">Today</div>
        <div className="text-2xl font-semibold text-white">{Math.round(today.calories_in ?? 0).toLocaleString()} kcal</div>
        <div className="text-[11px] text-white/40 mt-1">{entryCount} {entryCount === 1 ? 'entry' : 'entries'}</div>
      </div>
      <div className="sm:col-span-2 rounded-lg bg-white/[.02] border border-white/[.06] p-3 flex items-center gap-3">
        <div className="w-24 h-24 flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={macros} cx="50%" cy="50%" innerRadius={24} outerRadius={42} paddingAngle={2} dataKey="value">
                {macros.map((m) => <Cell key={m.name} fill={m.color} />)}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,.1)' }}
                formatter={(v: any, name: any) => [`${Number(v).toFixed(1)} g`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-2">
          {macros.map((m) => (
            <div key={m.name}>
              <div className="text-[10px] uppercase tracking-wider text-white/50 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: m.color }} />
                {m.name}
              </div>
              <div className="text-base font-semibold text-white">{Math.round(m.value)}<span className="text-xs text-white/40">g</span></div>
              <div className="text-[10px] text-white/40">{totalGrams > 0 ? Math.round((m.value / totalGrams) * 100) : 0}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CaloriesChart({ data }: { data: DailyNutrition[] }) {
  const chartData = useMemo(
    () => data.map((d) => ({ date: d.date.slice(5), calories: Math.round(d.calories_in ?? 0) })),
    [data],
  )

  if (chartData.length < 2) {
    return null
  }

  return (
    <div className="mt-2">
      <div className="text-[11px] uppercase tracking-wider text-white/50 mb-1">Calories</div>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
          <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
          <YAxis stroke="#9CA3AF" fontSize={11} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,.1)' }}
            formatter={(v: any) => [`${Number(v).toLocaleString()} kcal`, 'Calories']}
          />
          <Line type="monotone" dataKey="calories" stroke="#fbbf24" strokeWidth={2.5} dot={{ fill: '#fbbf24', r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function MacrosChart({ data }: { data: DailyNutrition[] }) {
  const chartData = useMemo(
    () => data.map((d) => ({
      date: d.date.slice(5),
      carbs: Math.round(d.carbs_g ?? 0),
      fat: Math.round(d.fat_g ?? 0),
      protein: Math.round(d.protein_g ?? 0),
    })),
    [data],
  )

  if (chartData.length < 2) {
    return null
  }

  return (
    <div className="mt-4">
      <div className="text-[11px] uppercase tracking-wider text-white/50 mb-1">Macros (g)</div>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.05)" />
          <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} />
          <YAxis stroke="#9CA3AF" fontSize={11} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,.1)' }}
            formatter={(v: any, name: any) => [`${v} g`, name]}
          />
          <Bar dataKey="carbs" stackId="m" fill={MACRO_COLORS.carbs} name="Carbs" />
          <Bar dataKey="fat" stackId="m" fill={MACRO_COLORS.fat} name="Fat" />
          <Bar dataKey="protein" stackId="m" fill={MACRO_COLORS.protein} name="Protein" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function LatestMealsList({ meals }: { meals: FoodEntry[] }) {
  if (meals.length === 0) return null

  return (
    <div className="mt-4">
      <div className="text-[11px] uppercase tracking-wider text-white/50 mb-2">Latest Entries</div>
      <ul className="divide-y divide-white/[.04] rounded-lg border border-white/[.06] bg-white/[.02]">
        {meals.map((m) => (
          <li key={`${m.external_id}-${m.date}`} className="px-3 py-2 flex items-center justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm text-white truncate">{m.food_entry_name}</div>
              <div className="text-[11px] text-white/40">
                {m.date} · {m.meal ? (MEAL_LABELS[m.meal.toLowerCase()] ?? m.meal) : 'Meal'}
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="text-sm font-semibold text-white">{Math.round(m.calories ?? 0)} kcal</div>
              <div className="text-[10px] text-white/40">
                {macroSnippet(m)}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function macroSnippet(m: FoodEntry): string {
  const parts: string[] = []
  if (m.carbs_g !== undefined) parts.push(`C ${Math.round(m.carbs_g)}`)
  if (m.fat_g !== undefined) parts.push(`F ${Math.round(m.fat_g)}`)
  if (m.protein_g !== undefined) parts.push(`P ${Math.round(m.protein_g)}`)
  return parts.join(' · ')
}

function filterToRangeDaily(data: DailyNutrition[], rangeDays: number): DailyNutrition[] {
  if (data.length === 0) return data
  const cutoff = new Date()
  cutoff.setUTCHours(0, 0, 0, 0)
  cutoff.setUTCDate(cutoff.getUTCDate() - (rangeDays - 1))
  const cutoffISO = cutoff.toISOString().slice(0, 10)
  return data.filter((d) => d.date >= cutoffISO)
}
