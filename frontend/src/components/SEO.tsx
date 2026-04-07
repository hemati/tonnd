import { Helmet } from 'react-helmet-async'

interface SEOProps {
  title?: string
  description?: string
  path?: string
  noindex?: boolean
}

const BASE_URL = 'https://tonnd.com'
const OG_IMAGE = `${BASE_URL}/og-image.png`
const DEFAULT_TITLE = 'TONND — Self-host your health dashboard'
const DEFAULT_DESC = 'Open-source, self-hosted health dashboard. Connect Fitbit and Renpho to track weight, sleep, heart rate, HRV, and body composition in one place.'

export default function SEO({ title, description, path = '/', noindex }: SEOProps) {
  const fullTitle = title ? `${title} — TONND` : DEFAULT_TITLE
  const desc = description || DEFAULT_DESC
  const url = `${BASE_URL}${path}`

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <link rel="canonical" href={url} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:url" content={url} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content={OG_IMAGE} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
      <meta name="twitter:image" content={OG_IMAGE} />
    </Helmet>
  )
}
