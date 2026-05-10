import type { ForwardRefExoticComponent, PropsWithoutRef, RefAttributes, SVGProps } from 'react'

export const CARD = 'bg-white/[.02] rounded-xl border border-white/[.06]'

export type HeroIcon = ForwardRefExoticComponent<
  PropsWithoutRef<SVGProps<SVGSVGElement>> & { title?: string; titleId?: string } & RefAttributes<SVGSVGElement>
>
