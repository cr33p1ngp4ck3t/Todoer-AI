# --- Builder Stage ---
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm config set registry https://registry.npmjs.org/ && \
    npm ci --legacy-peer-deps --no-optional --prefer-offline

# Copy source code
COPY . .

# Build application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- Production Stage ---
FROM node:20-slim

WORKDIR /app

# Copy built application from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Create non-root user
RUN groupadd -g 1001 nodejs && \
    useradd -u 1001 -g nodejs -m -s /bin/bash nextjs && \
    chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run application
CMD ["node", "server.js"]
