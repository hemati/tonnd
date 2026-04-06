# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Open a [GitHub Security Advisory](https://github.com/hemati/tonnd/security/advisories/new)
3. Include: description, steps to reproduce, potential impact

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

## Scope

- Authentication bypass
- Data exposure (user data, tokens)
- Injection vulnerabilities (SQL, XSS, command)
- Encryption weaknesses

## Out of Scope

- Denial of service
- Social engineering
- Issues in dependencies (report upstream)

## Security Practices

- JWT tokens with mandatory secret (app refuses to start without `JWT_SECRET`)
- Fitbit OAuth tokens encrypted at rest (Fernet)
- OAuth state parameters HMAC-signed with 10-minute expiry
- CORS restricted to configured frontend origin
- No secrets in git history
