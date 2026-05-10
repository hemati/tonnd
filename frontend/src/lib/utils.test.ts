import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn utility', () => {
  it('returns a single class unchanged', () => {
    expect(cn('text-red-500')).toBe('text-red-500')
  })

  it('merges multiple classes', () => {
    const result = cn('px-4', 'py-2', 'text-sm')
    expect(result).toContain('px-4')
    expect(result).toContain('py-2')
    expect(result).toContain('text-sm')
  })

  it('handles conditional classes via clsx syntax', () => {
    expect(cn('base', false && 'hidden')).toBe('base')
    expect(cn('base', true && 'visible')).toBe('base visible')
  })

  it('handles undefined and null inputs', () => {
    expect(cn('base', undefined, null)).toBe('base')
  })

  it('handles empty string input', () => {
    expect(cn('')).toBe('')
  })

  it('handles no arguments', () => {
    expect(cn()).toBe('')
  })

  it('deduplicates conflicting tailwind classes (last wins)', () => {
    // tailwind-merge should keep the last conflicting class
    expect(cn('px-2', 'px-4')).toBe('px-4')
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
  })

  it('merges conflicting bg classes', () => {
    expect(cn('bg-white', 'bg-black')).toBe('bg-black')
  })

  it('handles array inputs via clsx', () => {
    expect(cn(['px-2', 'py-2'])).toBe('px-2 py-2')
  })

  it('handles object inputs via clsx', () => {
    expect(cn({ 'text-red-500': true, hidden: false })).toBe('text-red-500')
  })
})
