ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim

WORKDIR /app

# Copy pyproject.toml and uv.lock from project root for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy the rest of the bot code
COPY . .

# Run the bot
CMD ["uv", "run", "bot.py"]
