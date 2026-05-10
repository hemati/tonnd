import { useState, type ReactNode } from 'react'
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'
import { cn } from '../lib/utils'

type HeroIcon = React.ForwardRefExoticComponent<React.PropsWithoutRef<React.SVGProps<SVGSVGElement>> & { title?: string; titleId?: string } & React.RefAttributes<SVGSVGElement>>

const CARD = 'bg-white/[.02] rounded-xl border border-white/[.06]'

export interface ExpandableCardProps {
  title: string
  icon: HeroIcon
  preview?: ReactNode
  headerExtra?: ReactNode
  children: ReactNode
  className?: string
}

export default function ExpandableCard({ title, icon: Icon, preview, headerExtra, children, className }: ExpandableCardProps) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className={cn(CARD, 'overflow-hidden', className)}>
      <button onClick={() => setExpanded(!expanded)}
        className="w-full p-6 flex items-center justify-between text-left hover:bg-white/[.01] transition-colors">
        <div className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-white/60" />
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          {headerExtra}
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
