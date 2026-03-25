# ---
# Stage 1: build the application
# ---

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace files for dependency installation
COPY pyproject.toml uv.lock ./
COPY bot/pyproject.toml ./bot/

# Install bot dependencies only
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --project bot

# Copy the bot directory
COPY bot ./bot

# Install the bot project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --project bot

# ---
# Stage 2: final image
# ---

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

USER nonroot

WORKDIR /app

CMD ["bot.py"]
