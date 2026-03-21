# Development Plan: LMS Telegram Bot

## Overview

This document outlines the implementation plan for building a Telegram bot that interfaces with the LMS (Learning Management System) backend. The bot enables users to check system health, browse labs and scores, and ask questions in natural language using an LLM for intent routing.

## Architecture

The bot follows a **layered architecture** with clear separation of concerns:

1. **Transport Layer** (`bot.py`) — Handles Telegram API communication via aiogram
2. **Handler Layer** (`handlers/`) — Command logic as pure functions, testable without Telegram
3. **Service Layer** (`services/`) — API client for LMS backend, LLM client for intent routing
4. **Configuration** (`config.py`) — Environment variable loading using pydantic-settings

This separation enables **testable handlers**: the same handler functions work in `--test` mode, unit tests, and production Telegram deployment.

## Task 1: Scaffold and Test Mode

Create the project skeleton with `--test` mode support. Handlers return placeholder text. The entry point accepts `--test "/command"` arguments, calls handlers directly, prints output to stdout, and exits cleanly. This enables offline development without Telegram connectivity.

## Task 2: Backend Integration

Implement real data fetching. Create an API client service that uses Bearer token authentication. Each slash command (`/health`, `/labs`, `/scores`) calls the appropriate LMS backend endpoint. Error handling ensures backend failures produce friendly messages rather than crashes. Configuration (URLs, API keys) comes from environment variables, never hardcoded.

## Task 3: Natural Language Intent Routing

Add LLM-powered intent routing. Users can ask questions in plain text ("what labs are available?"). The LLM receives tool descriptions for each available action and decides which tool to invoke. Tool description quality is critical — clear, precise descriptions matter more than prompt engineering. The same handler functions from Task 2 are called, but triggered by LLM tool calls instead of slash commands.

## Task 4: Containerization and Deployment

Package the bot as a Docker container. Add it as a service in `docker-compose.yml` alongside the existing backend. Document deployment steps: environment setup, container startup, verification. Ensure the bot runs persistently on the VM and responds to Telegram commands in production.

## Key Design Decisions

- **pydantic-settings** for configuration — type-safe, validates required env vars at startup
- **aiogram** for Telegram — async, modern, well-maintained
- **httpx** for HTTP client — async, supports Bearer auth naturally
- **Handler separation** — enables testing without Telegram, cleaner architecture
- **Environment-based config** — secrets never in code, different configs for dev/prod
