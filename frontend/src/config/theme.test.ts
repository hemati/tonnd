import { describe, it, expect } from 'vitest'
import { theme, LOGO_PATH, GITHUB_URL, DISCORD_URL } from './theme'

describe('theme constants', () => {
  it('pageBg uses #0a0a0a', () => {
    expect(theme.pageBg).toBe('bg-[#0a0a0a]')
  })

  it('heading includes font-bold and tracking-tight', () => {
    expect(theme.heading).toContain('font-bold')
    expect(theme.heading).toContain('tracking-tight')
  })

  it('btnPrimary is white bg with black text', () => {
    expect(theme.btnPrimary).toContain('bg-white')
    expect(theme.btnPrimary).toContain('text-black')
  })

  it('navBg uses sticky positioning with backdrop blur', () => {
    expect(theme.navBg).toContain('sticky')
    expect(theme.navBg).toContain('backdrop-blur')
  })

  it('LOGO_PATH is a valid SVG path starting with M', () => {
    expect(LOGO_PATH).toBe('M22 12h-4l-3 9L9 3l-3 9H2')
  })

  it('GITHUB_URL points to hemati/tonnd', () => {
    expect(GITHUB_URL).toBe('https://github.com/hemati/tonnd')
  })

  it('DISCORD_URL is a valid invite link', () => {
    expect(DISCORD_URL).toMatch(/^https:\/\/discord\.gg\//)
  })
})
