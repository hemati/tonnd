import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getPost } from '../lib/blog'
import { mdxComponents } from './blog/MdxComponents'
import SEO from './SEO'
import Logo from './Logo'
import Footer from './Footer'
import NotFound from './NotFound'

export default function BlogPost() {
  const { slug } = useParams<{ slug: string }>()
  const post = slug ? getPost(slug) : null

  if (!post) return <NotFound />

  const { meta, Component } = post

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      <SEO title={meta.title} description={meta.description} path={`/blog/${meta.slug}`} ogType="article" />
      {meta.image && (
        <Helmet>
          <meta property="og:image" content={`https://tonnd.com${meta.image}`} />
          <meta name="twitter:image" content={`https://tonnd.com${meta.image}`} />
        </Helmet>
      )}
      <Helmet>
        <script type="application/ld+json">{JSON.stringify({
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'BlogPosting',
              headline: meta.title,
              description: meta.description,
              datePublished: meta.date,
              dateModified: meta.date,
              image: meta.image ? `https://tonnd.com${meta.image}` : 'https://tonnd.com/og-image.png',
              author: { '@type': 'Person', name: meta.author, url: 'https://tonnd.com/' },
              publisher: { '@id': 'https://tonnd.com/#organization' },
              mainEntityOfPage: `https://tonnd.com/blog/${meta.slug}`,
              keywords: meta.tags.join(', '),
            },
            {
              '@type': 'BreadcrumbList',
              itemListElement: [
                { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://tonnd.com/' },
                { '@type': 'ListItem', position: 2, name: 'Blog', item: 'https://tonnd.com/blog' },
                { '@type': 'ListItem', position: 3, name: meta.title, item: `https://tonnd.com/blog/${meta.slug}` },
              ],
            },
          ],
        })}</script>
      </Helmet>

      <div className="max-w-5xl mx-auto px-5 w-full">
        <div className="h-14 flex items-center">
          <Logo />
        </div>
      </div>

      <article className="flex-1 max-w-5xl mx-auto px-5 py-16 w-full">
        <Link to="/blog" className="text-[13px] text-white/45 hover:text-white/70 transition-colors">&larr; All posts</Link>

        <header className="mt-6 mb-10">
          <h1 className="text-3xl font-bold mb-3">{meta.title}</h1>
          <div className="flex items-center gap-3 text-[13px] text-white/30">
            <span>{meta.author}</span>
            <span>&middot;</span>
            <time>{meta.date}</time>
          </div>
          {meta.tags.length > 0 && (
            <div className="flex gap-2 mt-3">
              {meta.tags.map((tag) => (
                <span key={tag} className="text-[11px] text-white/40 border border-white/[.08] rounded px-2 py-0.5">{tag}</span>
              ))}
            </div>
          )}
        </header>

        <div className="border-t border-white/[.06] pt-8">
          <Component components={mdxComponents as Record<string, React.ComponentType>} />
        </div>
      </article>

      <Footer />
    </div>
  )
}
