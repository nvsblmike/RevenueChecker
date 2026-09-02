# RevenueCheck Docker Compose deployment

This deployment runs Next.js and FastAPI in one non-root application container
and PostgreSQL in a separate private container. Only the application ports are
published. PostgreSQL is reachable solely on the internal Compose network.

## Server prerequisites

- Linux server with Docker Engine 27+ and Docker Compose v2
- A DNS record pointing at the server
- A host-level TLS reverse proxy forwarding the public domain to `127.0.0.1:3000`
- Outbound HTTPS access for Clerk/OpenAI and outbound SMTP access
- At least 2 GB RAM and 15 GB free disk

## Manual deployment

```bash
cd deploy
cp .env.example .env
chmod 600 .env
# Replace every placeholder in .env.
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 app
```

The application is available at `http://127.0.0.1:3000`; FastAPI is available
at `http://127.0.0.1:8000`. Keep these loopback-bound behind HTTPS in production.
Tables are created automatically after PostgreSQL becomes healthy.

## Operations

```bash
docker compose pull
docker compose up -d --remove-orphans
docker compose logs -f app
docker compose exec postgres pg_dump -U revenuecheck revenuecheck > backup.sql
```

Never commit `deploy/.env`, database dumps, private keys, or SMTP credentials.
