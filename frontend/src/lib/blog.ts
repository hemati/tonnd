export interface BlogPostMeta {
  title: string
  description: string
  date: string
  slug: string
  tags: string[]
  author: string
  image?: string
  faqs?: { q: string; a: string }[]
}

interface MdxModule {
  default: React.ComponentType<{ components?: Record<string, React.ComponentType> }>
  frontmatter: Record<string, unknown>
}

// Import all MDX files at build time (Vite glob)
const modules = import.meta.glob<MdxModule>('../../content/blog/*.mdx', { eager: true })

function parseMeta(fm: Record<string, unknown>, slug: string): BlogPostMeta {
  return {
    title: String(fm.title || ''),
    description: String(fm.description || ''),
    date: String(fm.date || ''),
    slug,
    tags: Array.isArray(fm.tags) ? fm.tags.map(String) : [],
    author: String(fm.author || 'Wahed Hemati'),
    image: fm.image ? String(fm.image) : undefined,
    faqs: Array.isArray(fm.faqs) ? fm.faqs : undefined,
  }
}

export function getAllPosts(): BlogPostMeta[] {
  return Object.entries(modules)
    .map(([path, mod]) => {
      const slug = path.split('/').pop()?.replace('.mdx', '') || ''
      return parseMeta(mod.frontmatter || {}, slug)
    })
    .filter((p) => p.title && p.date)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
}

export function getPost(slug: string): { meta: BlogPostMeta; Component: React.ComponentType<{ components?: Record<string, React.ComponentType> }> } | null {
  const entry = Object.entries(modules).find(([path]) =>
    path.endsWith(`/${slug}.mdx`)
  )
  if (!entry) return null

  const [, mod] = entry
  return {
    meta: parseMeta(mod.frontmatter || {}, slug),
    Component: mod.default,
  }
}
