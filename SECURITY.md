# Security Policy

## Supported Versions

This project is in active development. Security fixes are applied on the default branch.

## Reporting a Vulnerability

Please do not open public issues for suspected vulnerabilities.

Report privately via GitHub Security Advisories (preferred):
- Go to the repository page
- Open the Security tab
- Use "Report a vulnerability"

If private reporting is not available, contact the maintainer directly and include:
- A clear description of the issue
- Reproduction steps
- Impact assessment
- Suggested mitigation (if available)

## Handling Secrets and Data

- Never commit real customer data.
- Never commit `.env` files, credentials, private keys, or certificates.
- Use sanitized test fixtures only.
- Rotate any credential immediately if exposure is suspected.
