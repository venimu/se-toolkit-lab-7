FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml ./

# Install dependencies (uv will generate uv.lock if needed)
RUN uv sync

# Copy the rest of the bot code
COPY . .

# Run the bot
CMD ["uv", "run", "bot.py"]
