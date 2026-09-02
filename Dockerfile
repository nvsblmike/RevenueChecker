# syntax=docker/dockerfile:1.7
FROM node:22-bookworm-slim AS frontend-deps
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci

FROM frontend-deps AS frontend-build
WORKDIR /build
COPY next.config.ts tsconfig.json postcss.config.mjs eslint.config.mjs ./
COPY pages ./pages
COPY styles ./styles
COPY public ./public
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
ENV INTERNAL_API_BASE_URL=http://127.0.0.1:8000
ENV NEXT_TELEMETRY_DISABLED=1
RUN test -n "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" && npm run build

FROM node:22-bookworm-slim AS runtime
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    INTERNAL_API_BASE_URL=http://127.0.0.1:8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates curl \
    && python3 -m venv /opt/venv \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --home-dir /app app

COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY --from=frontend-build --chown=app:app /build/.next ./.next
COPY --from=frontend-build --chown=app:app /build/node_modules ./node_modules
COPY --from=frontend-build --chown=app:app /build/package.json ./package.json
COPY --from=frontend-build --chown=app:app /build/public ./public
COPY --chown=app:app api ./api
COPY --chown=app:app docker/entrypoint.sh /usr/local/bin/revenuecheck-entrypoint
RUN chmod 0555 /usr/local/bin/revenuecheck-entrypoint

USER app
EXPOSE 3000 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:3000/ >/dev/null \
      && curl --fail --silent http://127.0.0.1:8000/api >/dev/null || exit 1
ENTRYPOINT ["/usr/local/bin/revenuecheck-entrypoint"]
