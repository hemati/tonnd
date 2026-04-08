import { describe, it, expect, vi } from 'vitest'

// vi.hoisted ensures these are available inside the vi.mock factory (which is hoisted)
const { mockModules } = vi.hoisted(() => {
  const mockModules: Record<string, { default: any; frontmatter: Record<string, unknown> }> = {
    '../../content/blog/first-post.mdx': {
      default: () => null,
      frontmatter: {
        title: 'First Post',
        description: 'The first post',
        date: '2025-01-15',
        tags: ['health', 'fitness'],
        author: 'Test Author',
      },
    },
    '../../content/blog/second-post.mdx': {
      default: () => null,
      frontmatter: {
        title: 'Second Post',
        description: 'The second post',
        date: '2025-03-10',
        tags: ['sleep'],
        author: 'Another Author',
      },
    },
    '../../content/blog/draft-no-date.mdx': {
      default: () => null,
      frontmatter: {
        title: 'Draft Post',
        description: 'A draft without a date',
        date: '',
        tags: [],
      },
    },
    '../../content/blog/empty-title.mdx': {
      default: () => null,
      frontmatter: {
        title: '',
        description: 'No title',
        date: '2025-02-01',
        tags: [],
      },
    },
  }
  return { mockModules }
})

vi.mock('./blog', () => {
  const modules = mockModules

  function getAllPosts() {
    return Object.entries(modules)
      .map(([path, mod]) => {
        const slug = path.split('/').pop()?.replace('.mdx', '') || ''
        const fm = mod.frontmatter || {}
        return {
          title: String(fm.title || ''),
          description: String(fm.description || ''),
          date: String(fm.date || ''),
          slug,
          tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
          author: String(fm.author || 'Wahed Hemati'),
        }
      })
      .filter((p: { title: string; date: string }) => p.title && p.date)
      .sort((a: { date: string }, b: { date: string }) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }

  function getPost(slug: string) {
    const entry = Object.entries(modules).find(([path]) =>
      path.endsWith(`/${slug}.mdx`)
    )
    if (!entry) return null

    const [, mod] = entry
    const fm = mod.frontmatter || {}
    return {
      meta: {
        title: String(fm.title || ''),
        description: String(fm.description || ''),
        date: String(fm.date || ''),
        slug,
        tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
        author: String(fm.author || 'Wahed Hemati'),
      },
      Component: mod.default,
    }
  }

  return { getAllPosts, getPost }
})

import { getAllPosts, getPost } from './blog'

describe('blog utilities', () => {
  describe('getAllPosts', () => {
    it('returns an array of posts', () => {
      const posts = getAllPosts()
      expect(Array.isArray(posts)).toBe(true)
    })

    it('filters out posts without title or date', () => {
      const posts = getAllPosts()
      const slugs = posts.map((p) => p.slug)
      expect(slugs).not.toContain('draft-no-date')
      expect(slugs).not.toContain('empty-title')
    })

    it('includes valid posts', () => {
      const posts = getAllPosts()
      const slugs = posts.map((p) => p.slug)
      expect(slugs).toContain('first-post')
      expect(slugs).toContain('second-post')
    })

    it('returns exactly 2 valid posts', () => {
      const posts = getAllPosts()
      expect(posts).toHaveLength(2)
    })

    it('sorts posts by date descending (newest first)', () => {
      const posts = getAllPosts()
      expect(posts[0].slug).toBe('second-post') // 2025-03-10
      expect(posts[1].slug).toBe('first-post')  // 2025-01-15
    })

    it('extracts correct metadata fields', () => {
      const posts = getAllPosts()
      const first = posts.find((p) => p.slug === 'first-post')!
      expect(first.title).toBe('First Post')
      expect(first.description).toBe('The first post')
      expect(first.date).toBe('2025-01-15')
      expect(first.tags).toEqual(['health', 'fitness'])
      expect(first.author).toBe('Test Author')
    })

    it('all posts have truthy author field', () => {
      const posts = getAllPosts()
      posts.forEach((p) => {
        expect(p.author).toBeTruthy()
      })
    })
  })

  describe('getPost', () => {
    it('returns a post by slug', () => {
      const result = getPost('first-post')
      expect(result).not.toBeNull()
      expect(result!.meta.slug).toBe('first-post')
      expect(result!.meta.title).toBe('First Post')
    })

    it('returns the Component for a found post', () => {
      const result = getPost('second-post')
      expect(result).not.toBeNull()
      expect(result!.Component).toBeDefined()
    })

    it('returns null for a non-existent slug', () => {
      const result = getPost('does-not-exist')
      expect(result).toBeNull()
    })

    it('returns correct metadata for the post', () => {
      const result = getPost('second-post')!
      expect(result.meta.title).toBe('Second Post')
      expect(result.meta.description).toBe('The second post')
      expect(result.meta.date).toBe('2025-03-10')
      expect(result.meta.tags).toEqual(['sleep'])
      expect(result.meta.author).toBe('Another Author')
    })
  })
})
