# ─────────────────────────────────────────────────────────────────────────────
# AASI Frontend — Production Multi-Stage Next.js Build
# Image: node:20-alpine
# Security: Non-root user, standalone output, minimal attack surface
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# Stage 3: Production runtime
FROM node:20-alpine AS runner
WORKDIR /app

LABEL maintainer="AASI Engineering <engineering@projectpolaris.in>"
LABEL org.opencontainers.image.title="AASI Frontend"
LABEL org.opencontainers.image.description="Autonomous Aerospace Scientific Intelligence — Mission Control Cockpit"
LABEL org.opencontainers.image.version="1.0.0"

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user
RUN addgroup --system --gid 1001 aasi \
    && adduser --system --uid 1001 aasi

# Copy build artifacts
COPY --from=builder /app/public ./public
COPY --from=builder --chown=aasi:aasi /app/.next/standalone ./
COPY --from=builder --chown=aasi:aasi /app/.next/static ./.next/static

USER aasi

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
