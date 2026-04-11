import { useState } from 'react'
import Body, { type ExtendedBodyPart, type Slug } from '@mjcdev/react-body-highlighter'

interface MuscleMapProps {
  muscleGroups: Record<string, number>
  exercisesByGroup?: Record<string, string[]>
  className?: string
}

// Map Hevy muscle group names → body-highlighter SVG slugs
const HEVY_TO_SLUG: Record<string, Slug[]> = {
  // Hevy primary_muscle names
  chest: ['chest'],
  lats: ['upper-back'],
  upper_back: ['upper-back'],
  lower_back: ['lower-back'],
  quadriceps: ['quadriceps'],
  hamstrings: ['hamstring'],
  glutes: ['gluteal'],
  calves: ['calves'],
  shoulders: ['deltoids'],
  traps: ['trapezius'],
  biceps: ['biceps'],
  triceps: ['triceps'],
  forearms: ['forearm'],
  abdominals: ['abs'],
  obliques: ['obliques'],
  adductors: ['adductors'],
  // Our old group names (backward compat)
  back: ['upper-back', 'lower-back'],
  legs: ['quadriceps', 'hamstring', 'calves', 'gluteal'],
  core: ['abs', 'obliques'],
}

// Reverse map: slug → Hevy muscle group name (for tooltip lookup)
const SLUG_TO_GROUP: Record<string, string> = {}
for (const [group, slugs] of Object.entries(HEVY_TO_SLUG)) {
  for (const slug of slugs) {
    if (!SLUG_TO_GROUP[slug]) SLUG_TO_GROUP[slug] = group
  }
}

function buildBodyData(muscleGroups: Record<string, number>) {
  const maxSets = Math.max(...Object.values(muscleGroups), 1)
  const data: { slug: Slug; intensity: number }[] = []

  for (const [group, sets] of Object.entries(muscleGroups)) {
    const slugs = HEVY_TO_SLUG[group] || []
    const ratio = sets / maxSets
    const intensity = ratio > 0.8 ? 5 : ratio > 0.6 ? 4 : ratio > 0.4 ? 3 : ratio > 0.2 ? 2 : 1

    for (const slug of slugs) {
      data.push({ slug, intensity })
    }
  }
  return data
}

export default function MuscleMap({ muscleGroups, exercisesByGroup, className = '' }: MuscleMapProps) {
  const data = buildBodyData(muscleGroups)
  const [tooltip, setTooltip] = useState<{ group: string; sets: number; exercises: string[] } | null>(null)

  const handleClick = (part: ExtendedBodyPart) => {
    const slug = part.slug
    if (!slug) return
    const group = SLUG_TO_GROUP[slug]
    if (!group) return

    const sets = muscleGroups[group] || 0
    const exercises = exercisesByGroup?.[group] || []

    if (tooltip?.group === group) {
      setTooltip(null)
    } else {
      setTooltip({ group, sets, exercises })
    }
  }

  return (
    <div className={className}>
      <div className="flex justify-center items-start gap-4">
        <div style={{ maxWidth: '160px' }}>
          <Body
            data={data}
            side="front"
            gender="male"
            scale={1}
            colors={['#0c4a5e', '#0e7490', '#06b6d4', '#22d3ee', '#67e8f9']}
            border="#1e293b"
            onBodyPartClick={handleClick}
          />
          <p className="text-center text-white/30 text-xs mt-1">Front</p>
        </div>
        <div style={{ maxWidth: '160px' }}>
          <Body
            data={data}
            side="back"
            gender="male"
            scale={1}
            colors={['#0c4a5e', '#0e7490', '#06b6d4', '#22d3ee', '#67e8f9']}
            border="#1e293b"
            onBodyPartClick={handleClick}
          />
          <p className="text-center text-white/30 text-xs mt-1">Back</p>
        </div>
      </div>

      {tooltip && (
        <div className="mt-3 bg-white/[.06] rounded-lg p-3 text-sm">
          <div className="flex justify-between items-center mb-1">
            <span className="text-white font-medium capitalize">{tooltip.group}</span>
            <span className="text-white/40">{tooltip.sets} sets</span>
          </div>
          {tooltip.exercises.length > 0 ? (
            <ul className="text-white/50 text-xs space-y-0.5">
              {tooltip.exercises.map((ex, i) => (
                <li key={i}>· {ex}</li>
              ))}
            </ul>
          ) : (
            <p className="text-white/30 text-xs">No exercises tracked</p>
          )}
        </div>
      )}

      {!tooltip && (
        <p className="text-center text-white/20 text-xs mt-3">Click a muscle group for details</p>
      )}
    </div>
  )
}
