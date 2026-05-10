import { ScaleIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import ExpandableCard from './ExpandableCard'
import { useBodyMeasurements, useLatestBodyMeasurement } from '../hooks/useQueries'
import { detectDataState, daysBetween } from '../lib/bodyComposition'
import type { BodyMeasurement } from '../services/api'

interface BodyCompositionCardProps {
  rangeDays: 7 | 14 | 30
}

export default function BodyCompositionCard({ rangeDays }: BodyCompositionCardProps) {
  const range = useBodyMeasurements(rangeDays)
  const latest = useLatestBodyMeasurement()

  if (range.isLoading || latest.isLoading) {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <div className="mt-4 animate-pulse text-white/40 text-sm">Loading...</div>
      </div>
    )
  }

  const rangeData = range.data?.data ?? []
  const latestData = latest.data?.data ?? []
  const state = detectDataState(rangeData, latestData)

  if (state === 'no-data-ever') {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <NoDataEver />
      </div>
    )
  }

  if (state === 'no-data-in-range') {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.06] bg-white/[.02] p-5">
        <EmptyHeader rangeDays={rangeDays} />
        <NoDataInRange rangeDays={rangeDays} latest={latestData[0]} />
      </div>
    )
  }

  // Placeholder for other states — filled in by Tasks 10-13
  return (
    <div data-testid="body-card-root">
      <ExpandableCard title="Body Composition" icon={ScaleIcon}>
        <p className="text-white/40 text-xs">{rangeDays}-day trend</p>
      </ExpandableCard>
    </div>
  )
}

// Used by loading + empty-state shells (which don't use ExpandableCard,
// so they need their own header rendering).
function EmptyHeader({ rangeDays }: { rangeDays: number }) {
  return (
    <div className="flex justify-between items-start">
      <div>
        <h3 className="text-white font-semibold text-base">Body Composition</h3>
        <p className="text-white/40 text-xs mt-1">{rangeDays}-day trend</p>
      </div>
      <span className="bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full text-[10px]">Renpho</span>
    </div>
  )
}

function NoDataEver() {
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">Renpho needed for muscle mass and lean body mass tracking</p>
      <Link
        to="/sources#renpho"
        className="inline-block mt-4 px-4 py-2 bg-cyan-500/10 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/20"
      >
        Connect Renpho
      </Link>
    </div>
  )
}

function NoDataInRange({ rangeDays, latest }: { rangeDays: number; latest: BodyMeasurement }) {
  const daysSince = daysBetween(latest.measured_at, new Date().toISOString())
  return (
    <div className="mt-6 text-center py-8">
      <p className="text-white/60 text-sm">No measurements in last {rangeDays} days.</p>
      <p className="text-white/40 text-xs mt-1">Last measurement was {daysSince} days ago.</p>
    </div>
  )
}
