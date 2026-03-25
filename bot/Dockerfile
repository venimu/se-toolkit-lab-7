ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim

WORKDIR /app

# Copy pyproject.toml and uv.lock from project root for dependency installation
COPY pyproject.toml uv.lock ./
COPY bot/pyproject.toml ./bot/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy the rest of the bot code
COPY bot .

# Run the bot
CMD ["uv", "run", "bot.py"]
