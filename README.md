# RevenueCheck by t-Consult

A focused SME revenue-leakage assessment built with Next.js, Clerk and FastAPI.

## One-time setup

```bash
npm install
cp .env.example .env.local
```

Replace the Clerk placeholders in `.env.local` with keys from your Clerk
dashboard. Next.js loads `.env.local` automatically. Never commit it.

Also add your `OPENAI_API_KEY`, `OPENAI_MODEL` and Clerk `CLERK_JWKS_URL`. The
Python API loads this same local environment file; keys remain server-side.

## Database and report email

RevenueCheck requires a PostgreSQL database. Create an empty database and set:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/revenuecheck?sslmode=require
```

FastAPI creates `app_users`, `assessments`, and `email_deliveries` on startup.
The equivalent SQL is available in `api/schema.sql` if your provider requires
manual migrations.

To email completed, consented assessments to t-Consult, configure Resend:

```env
RESEND_API_KEY=re_replace_me
RESEND_FROM_EMAIL=RevenueCheck <reports@your-verified-domain.com>
REPORT_RECIPIENT_EMAIL=alesemichael641@gmail.com
```

The API saves the assessment before returning it. Email is sent in a background
task, and every delivery attempt is recorded as `sent` or `failed` so an email
outage does not lose the report.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
```

## Run locally

Terminal 1 — FastAPI:

```bash
source .venv/bin/activate
uvicorn api.index:app --reload --port 8000
```

Terminal 2 — Next.js:

```bash
npm run dev
```

Open http://localhost:3000. In development, Next.js proxies `/api` to
`http://127.0.0.1:8000/api`, so the frontend uses the same URL locally and on
Vercel.

- Frontend: http://localhost:3000
- API health check: http://localhost:8000/api
- Interactive API docs: http://localhost:8000/docs

## Clerk keys

`ClerkProvider` receives `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` in
`pages/_app.tsx`. Clerk's server-side utilities read `CLERK_SECRET_KEY`
automatically when needed. Never pass the secret key to React or expose it with
a `NEXT_PUBLIC_` prefix.
# RevenueChecker
