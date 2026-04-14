import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { getAllPosts } from '../lib/blog'
import SEO from './SEO'
import Logo from './Logo'
import Footer from './Footer'

export default function BlogIndex() {
  const posts = getAllPosts()

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <SEO title="Blog" description="Articles about self-hosted health tracking, fitness data, and open-source development." path="/blog" />
      <Helmet>
        <script type="application/ld+json">{JSON.stringify({
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'CollectionPage',
              '@id': 'https://tonnd.com/blog',
              'name': 'Blog — TONND',
              'description': 'Articles about self-hosted health tracking, fitness data, and open-source development.',
              'url': 'https://tonnd.com/blog',
              'isPartOf': { '@id': 'https://tonnd.com/#website' }
            },
            {
              '@type': 'BreadcrumbList',
              'itemListElement': [
                { '@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': 'https://tonnd.com/' },
                { '@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': 'https://tonnd.com/blog' }
              ]
            },
            {
              '@type': 'ItemList',
              'itemListElement': posts.map((post, i) => ({
                '@type': 'ListItem',
                'position': i + 1,
                'url': `https://tonnd.com/blog/${post.slug}`
              }))
            }
          ]
        })}</script>
      </Helmet>

      <div className="max-w-5xl mx-auto px-5">
        <div className="h-14 flex items-center">
          <Logo />
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-5 py-16">
        <h1 className="text-3xl font-bold mb-2">Blog</h1>
        <p className="text-[15px] text-white/40 mb-12">Thoughts on health data, self-hosting, and building in the open.</p>

        {posts.length === 0 ? (
          <p className="text-white/30">No posts yet.</p>
        ) : (
          <div className="space-y-1">
            {posts.map((post) => (
              <Link
                key={post.slug}
                to={`/blog/${post.slug}`}
                className="block rounded-lg p-4 -mx-4 hover:bg-white/[.03] transition-colors"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <h2 className="text-base font-semibold text-white/80">{post.title}</h2>
                  <time className="text-[13px] text-white/25 flex-shrink-0">{post.date}</time>
                </div>
                <p className="text-sm text-white/40 mt-1 line-clamp-2">{post.description}</p>
              </Link>
            ))}
          </div>
        )}

      </div>

      <Footer />
    </div>
  )
}
