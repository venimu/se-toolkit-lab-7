ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim

WORKDIR /app

# Copy workspace files for dependency installation
COPY pyproject.toml uv.lock ./
COPY bot/pyproject.toml ./bot/
COPY backend/pyproject.toml ./backend/

# Install all workspace dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy the bot directory
COPY bot ./bot

# Install the bot project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Run the bot
CMD ["uv", "run", "--project", "bot", "bot.py"]
