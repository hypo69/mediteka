# Security Policy

## Supported Versions

Only the current release branch receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.7.x   | :white_check_mark: |
| < 0.7   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not open a public GitHub issue**.

Report it privately:

- **GitHub**: use [Security Advisories](https://github.com/hypo69/FastApiFoundry-Docker/security/advisories/new)
- **Email**: contact the maintainer via the GitHub profile

### What to include

- Description of the vulnerability
- Steps to reproduce
- Affected version
- Potential impact

### Response timeline

- Acknowledgement within **3 business days**
- Fix or mitigation within **14 days** for critical issues
- Public disclosure after the fix is released

## Security Considerations

This project runs **locally** and is not designed for public internet exposure by default.

Key points:

- Установка `API_KEY` в `.env` для ограничения доступа к REST API
- Do not expose port `9696` to the internet without a reverse proxy and authentication
- Keep `.env` out of version control — it is listed in `.gitignore`
- Tokens (`HF_TOKEN`, `TELEGRAM_*`, `FTP_*`) are secrets — never commit them
