import { Helmet } from 'react-helmet-async'

interface SEOProps {
  title?: string
  description?: string
  path?: string
  noindex?: boolean
}

const BASE_URL = 'https://tonnd.com'
const DEFAULT_TITLE = 'TONND — Self-host your health dashboard'
const DEFAULT_DESC = 'Open-source, self-hosted health dashboard. Connect Fitbit and Renpho, see all your metrics in one place.'

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
      <meta name="twitter:card" content="summary" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
    </Helmet>
  )
}
