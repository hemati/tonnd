import fitbitSvg from '../assets/icons/fitbit.svg'
import renphoSvg from '../assets/icons/renpho.svg'
import hevySvg from '../assets/icons/hevy.svg'

const ICON_STYLE = { filter: 'invert(1) opacity(0.5)' } as const

interface SourceIconProps {
  className?: string
}

function SourceIcon({ src, alt, className = 'w-8 h-8' }: { src: string; alt: string; className?: string }) {
  return <img src={src} alt={alt} className={className} style={ICON_STYLE} />
}

export const FitbitIcon = (p: SourceIconProps) => <SourceIcon src={fitbitSvg} alt="Fitbit" {...p} />
export const RenphoIcon = (p: SourceIconProps) => <SourceIcon src={renphoSvg} alt="Renpho" {...p} />
export const HevyIcon = (p: SourceIconProps) => <SourceIcon src={hevySvg} alt="Hevy" {...p} />
