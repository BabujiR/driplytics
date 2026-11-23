# syntax=docker/dockerfile:1.7
# One image recipe for every Python service in the uv workspace.
#   docker build -f infra/docker/python.Dockerfile --build-arg PACKAGE=driplytics-api .
FROM python:3.12-slim

# uv: fast installer/resolver (ADR 0002). Pin a specific version once uv.lock is committed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG PACKAGE
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Workspace manifests first (better layer caching), then sources.
# uv.loc[k] matches uv.lock if it exists and is skipped if not.
COPY pyproject.toml .python-version uv.loc[k] ./
COPY engine engine
COPY apps/api apps/api
COPY services/worker services/worker

# Install only the requested package and its workspace dependencies (worker -> engine).
# Switch to `uv sync --locked ...` once uv.lock is committed.
RUN --mount=type=cache,target=/root/.cache/uv \
    test -n "$PACKAGE" && uv sync --package "$PACKAGE" --no-dev

RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app
