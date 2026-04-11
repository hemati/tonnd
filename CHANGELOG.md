# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Hevy workout tracking integration (API key, sync, muscle group detection)
- Renpho body composition integration (weight, body fat, muscle mass)
- Multi-source sync architecture (`source` column on fitness_metrics)
- Sources page to connect/disconnect Fitbit, Renpho, Hevy
- Bento-grid dashboard with recovery breakdown, EWMA trends, staleness indicators
- Sleep-HRV correlation chart
- Expandable metric cards
- Navbar with Dashboard/Sources navigation
- Blog infrastructure (MDX-based)
- Blog post: "Fitbit killed the dashboard. So I built my own."
- GA4 analytics (consent-aware)
- SEO: React Helmet, schema.org, canonical URLs, sitemap
- About page
- Cookie consent banner (GDPR)
- Legal pages (Privacy Policy, Terms of Service, Cookie Policy)
- Unit tests: 94% backend coverage, 95% frontend coverage
- CI/CD: GitHub Actions (tests, lint, type-check)
- Codecov integration
- Issue and PR templates
- Discord community link

### Changed
- Migrated from AWS (Lambda, DynamoDB, Cognito) to FastAPI + PostgreSQL + Docker
- Auth: fastapi-users with JWT + Google OAuth (replaced AWS Cognito + Amplify)
- Frontend: standard JWT auth with localStorage (replaced AWS Amplify)
- Services restructured into subdirectories (fitbit/, renpho/, hevy/)
- Dashboard redesigned with monochrome design system
- Landing page rewritten for managed + self-hosted audiences

### Fixed
- Fitbit token refresh crash on expired tokens
- Scheduler eager load error (added .unique())
- Soft 404s and nginx trailing-slash redirects
- Accessibility: aria-labels, heading hierarchy

### Security
- Removed leaked credentials from git history
- JWT secrets fail-hard on startup (no insecure defaults)
- Fitbit tokens encrypted at rest with Fernet
- Security headers (HSTS, CSP, X-Frame-Options)
