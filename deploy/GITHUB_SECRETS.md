# GitHub Actions production secrets

Add these under **Repository settings → Secrets and variables → Actions**.
Protect the `production` environment with required reviewers.

## Server access

- `SERVER_HOST`: server hostname or IP
- `SERVER_USER`: non-root deployment user in the Docker group
- `SERVER_SSH_PORT`: SSH port, normally `22`
- `SERVER_SSH_KEY`: private Ed25519 deployment key
- `DEPLOY_PATH`: absolute server directory, e.g. `/opt/revenuecheck`
- `GHCR_USERNAME`: GitHub account allowed to pull the image
- `GHCR_PAT`: fine-grained token with read-only Packages permission

## Application

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (public configuration, stored here for pipeline convenience)
- `CLERK_SECRET_KEY`
- `CLERK_JWKS_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (e.g. `gpt-5-mini`)
- `NEXT_PUBLIC_BOOKING_URL`

## PostgreSQL

- `POSTGRES_DB` (e.g. `revenuecheck`)
- `POSTGRES_USER` (e.g. `revenuecheck`)
- `POSTGRES_PASSWORD` (generate at least 32 random characters)

## Resend

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL` (sender on your verified domain, e.g. `RevenueCheck <reports@example.com>`)
- `REPORT_RECIPIENT_EMAIL` (`alesemichael641@gmail.com`)

Do not use personal SSH keys, database passwords reused elsewhere, or a GitHub PAT
with repository write permissions.
