import { ScaleIcon } from '@heroicons/react/24/outline'
import ExpandableCard from './ExpandableCard'
import { useBodyMeasurements, useLatestBodyMeasurement } from '../hooks/useQueries'

interface BodyCompositionCardProps {
  rangeDays: 7 | 14 | 30
}

export default function BodyCompositionCard({ rangeDays }: BodyCompositionCardProps) {
  const range = useBodyMeasurements(rangeDays)
  const latest = useLatestBodyMeasurement()

  if (range.isLoading || latest.isLoading) {
    return (
      <div data-testid="body-card-root" className="rounded-xl border border-white/[.08] bg-white/[.02] p-5">
        <h3 className="text-white font-semibold text-base">Body Composition</h3>
        <div className="mt-4 animate-pulse text-white/40 text-sm">Loading...</div>
      </div>
    )
  }

  // Scaffold: always render ExpandableCard for now — Task 9 adds the real
  // state branches (no-data-ever / no-data-in-range / single-point / full).
  return (
    <div data-testid="body-card-root">
      <ExpandableCard title="Body Composition" icon={ScaleIcon}>
        <p className="text-white/40 text-xs">{rangeDays}-day trend</p>
      </ExpandableCard>
    </div>
  )
}
