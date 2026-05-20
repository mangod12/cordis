# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Email security concerns to the maintainers directly. Include:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Measures

Cordis implements:
- JWT authentication (HS256) on all API endpoints
- Rate limiting (30 requests/minute on emergency endpoint)
- CORS origin validation (no wildcards)
- Input validation (audio size limits, transcript length limits, MIME type checks)
- SQL injection prevention (SQLAlchemy ORM, parameterized queries)
- Security headers middleware
- Environment-based configuration (no hardcoded secrets)
- Production guards (SQLite blocked, docs disabled, wildcard CORS rejected)

## Best Practices for Deployment

1. Set a strong `SECRET_KEY` (minimum 32 characters, random)
2. Use PostgreSQL in production (`USE_SQLITE=false`)
3. Configure specific CORS origins (`ALLOWED_ORIGINS`)
4. Run behind a reverse proxy (nginx/Caddy) with TLS
5. Rotate JWT tokens (default expiry: 120 minutes)
6. Keep dependencies updated (`pip install --upgrade -r requirements.txt`)
