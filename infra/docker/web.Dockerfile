# syntax=docker/dockerfile:1.7
# Local development image for the Next.js web app (hot reload). A production image comes with P0-23.
FROM node:22-alpine

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NEXT_TELEMETRY_DISABLED=1
RUN corepack enable

WORKDIR /app

# pnpm-lock.yam[l] matches the lockfile if it exists and is skipped if not.
COPY package.json pnpm-workspace.yaml turbo.json tsconfig.base.json pnpm-lock.yam[l] ./
COPY apps/web/package.json apps/web/
COPY packages/ui/package.json packages/ui/
COPY packages/contracts/package.json packages/contracts/
RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store \
    pnpm install

COPY apps/web apps/web
COPY packages packages

EXPOSE 3000
CMD ["pnpm", "--filter", "@driplytics/web", "dev", "--hostname", "0.0.0.0"]
