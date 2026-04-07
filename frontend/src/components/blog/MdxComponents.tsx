import type { ComponentPropsWithoutRef } from 'react'

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

function Heading({ level, children, ...props }: { level: 2 | 3; children?: React.ReactNode } & ComponentPropsWithoutRef<'h2'>) {
  const text = typeof children === 'string' ? children : ''
  const id = slugify(text)
  const Tag = `h${level}` as 'h2' | 'h3'
  const styles = level === 2
    ? 'text-xl font-bold text-white/90 mt-10 mb-4'
    : 'text-lg font-semibold text-white/80 mt-8 mb-3'

  return (
    <Tag id={id} className={styles} {...props}>
      <a href={`#${id}`} className="hover:text-white/60 no-underline">{children}</a>
    </Tag>
  )
}

export const mdxComponents = {
  h1: (props: ComponentPropsWithoutRef<'h1'>) => (
    <h1 className="text-3xl font-bold text-white mt-0 mb-6" {...props} />
  ),
  h2: (props: ComponentPropsWithoutRef<'h2'>) => <Heading level={2} {...props} />,
  h3: (props: ComponentPropsWithoutRef<'h3'>) => <Heading level={3} {...props} />,
  p: (props: ComponentPropsWithoutRef<'p'>) => (
    <p className="text-[15px] text-white/50 leading-relaxed mb-4" {...props} />
  ),
  a: ({ href, children, ...props }: ComponentPropsWithoutRef<'a'>) => {
    const isExternal = href?.startsWith('http')
    return (
      <a
        href={href}
        className="text-white/70 underline hover:text-white transition-colors"
        {...(isExternal ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
        {...props}
      >
        {children}
      </a>
    )
  },
  ul: (props: ComponentPropsWithoutRef<'ul'>) => (
    <ul className="list-disc list-inside space-y-1.5 mb-4 text-[15px] text-white/50" {...props} />
  ),
  ol: (props: ComponentPropsWithoutRef<'ol'>) => (
    <ol className="list-decimal list-inside space-y-1.5 mb-4 text-[15px] text-white/50" {...props} />
  ),
  li: (props: ComponentPropsWithoutRef<'li'>) => (
    <li className="leading-relaxed" {...props} />
  ),
  blockquote: (props: ComponentPropsWithoutRef<'blockquote'>) => (
    <blockquote className="border-l-2 border-white/[.15] pl-4 my-4 text-white/40 italic" {...props} />
  ),
  code: (props: ComponentPropsWithoutRef<'code'>) => (
    <code className="text-white/60 bg-white/[.06] px-1.5 py-0.5 rounded text-[13px] font-mono" {...props} />
  ),
  pre: (props: ComponentPropsWithoutRef<'pre'>) => (
    <pre className="bg-white/[.03] border border-white/[.06] rounded-lg p-4 overflow-x-auto mb-4 text-[13px]" {...props} />
  ),
  strong: (props: ComponentPropsWithoutRef<'strong'>) => (
    <strong className="text-white/80 font-semibold" {...props} />
  ),
  hr: () => <hr className="border-white/[.06] my-8" />,
}
