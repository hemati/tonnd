/**
 * Shared design tokens for the monochrome TONND design system.
 * Reuse these across LandingPage, Login, Layout, Dashboard.
 */

/* Tailwind class strings — import and spread into className */

export const theme = {
  /* page backgrounds */
  pageBg: 'bg-[#0a0a0a]',
  cardBg: 'bg-white/[.02]',
  cardBorder: 'border border-white/[.06]',
  divider: 'border-t border-white/[.06]',

  /* text hierarchy */
  heading: 'text-white font-bold tracking-tight',
  body: 'text-white/65',
  label: 'text-[13px] text-white/40 font-medium tracking-wide',
  muted: 'text-white/35',

  /* inputs */
  input: 'w-full px-4 py-2.5 rounded-md bg-white/[.04] border border-white/[.1] text-white placeholder-white/25 text-sm focus:outline-none focus:border-white/25 transition-colors',

  /* buttons */
  btnPrimary: 'inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium bg-white text-black hover:bg-white/90 transition-colors',
  btnSecondary: 'inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium border border-white/[.12] text-white/60 hover:text-white hover:border-white/25 transition-colors',
  btnGhost: 'text-sm text-white/50 hover:text-white/80 transition-colors',

  /* nav */
  navBg: 'sticky top-0 z-50 border-b border-white/[.06] bg-[#0a0a0a]/80 backdrop-blur-xl',
  navContainer: 'max-w-5xl mx-auto px-5 h-14 flex items-center justify-between',
  navLink: 'text-[13px] text-white/50 hover:text-white/80 transition-colors',

  /* containers */
  container: 'max-w-5xl mx-auto px-5',
  section: 'py-8',
} as const

/** TONND heartbeat logo SVG path */
export const LOGO_PATH = 'M22 12h-4l-3 9L9 3l-3 9H2'

/** Brand constants */
export const GITHUB_URL = 'https://github.com/hemati/tonnd'
export const DISCORD_URL = 'https://discord.gg/3qmrFpwzpE'
