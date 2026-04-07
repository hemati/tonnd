import { describe, it, expect } from 'vitest'
import { theme, LOGO_PATH, GITHUB_URL, DISCORD_URL } from './theme'

describe('theme constants', () => {
  it('has required theme tokens', () => {
    expect(theme.pageBg).toBeDefined()
    expect(theme.heading).toBeDefined()
    expect(theme.btnPrimary).toBeDefined()
    expect(theme.input).toBeDefined()
  })

  it('LOGO_PATH is a valid SVG path', () => {
    expect(LOGO_PATH).toContain('M')
    expect(LOGO_PATH.length).toBeGreaterThan(10)
  })

  it('GITHUB_URL points to correct repo', () => {
    expect(GITHUB_URL).toBe('https://github.com/hemati/tonnd')
  })

  it('DISCORD_URL is a valid invite link', () => {
    expect(DISCORD_URL).toMatch(/^https:\/\/discord\.gg\//)
  })
})
