# Copilot Instructions — Ravebot

## Architecture

Ravebot is a **Telegram bot** for a music community group, built with `python-telegram-bot` v20.6 (async). The active code lives in `apps/bot/`. The `apps/updater/` and `api/dice/` directories are inactive/empty.

The bot integrates three external services:

- **Teamup API** (`events_calendar.py`) — calendar CRUD for community events
- **RA.co** (`ra.py`) — event scraping via GraphQL
- **Dice.fm** (`dice.py`) — event scraping via REST API + HTML parsing

Core flows:

- **Member onboarding**: new member joins → welcome message → must post `#whois` within 2 hours or gets kicked. Managed via `context.chat_data`/`context.user_data` and the `job_queue` scheduler.
- **Event creation**: `/createevent <url>` → validate URL → scrape event from RA/Dice → check for duplicates in Teamup → create via API. Rate-limited (3/60s per user).
- **Event announcements**: `/rave` returns cached weekly events. Cache stored in `context.chat_data['cache']` via `PicklePersistence`.

State is persisted to a local pickle file (`bot_data`) — there is no external database.

## Running the Bot

```bash
cd apps/bot
pip install -r requirements.txt
cp ../../.env.example .env  # fill in credentials
python main.py
```

The bot runs in long-polling mode (no webhooks).

## Testing

pytest, pytest-asyncio, and pytest-mock are in `requirements.txt` but no test files currently exist. To run tests when added:

```bash
cd apps/bot
pytest               # full suite
pytest tests/test_utils.py -k "test_validate_url"  # single test
```

## Deployment

- **Azure Container Apps**: manual trigger via `.github/workflows/azure-deploy.yml`. Builds Docker image → pushes to ACR → deploys to Container Apps.

Uses `apps/bot/Dockerfile` (Python 3.11-slim, non-root user, health check).

## Conventions

### Configuration

Settings are loaded at import time in `settings.py` via `dotenv_values()` + `os.environ` (env vars override `.env`). Dev/prod switching is controlled by `ENVIRONMENT` env var — when set to `dev`, `BOT_TOKEN_DEV` and `TEAMUP_API_KEY_DEV` are used instead of production keys.

### Error Handling

All external API calls follow a **log-and-continue** pattern: catch exceptions, log the error, return `None` or empty list. The bot never crashes from a failed API call.

### Async Handlers

All Telegram command handlers are `async` functions with the signature:

```python
async def command_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
```

### User-Facing Messages

All message templates live in `text.py` and are primarily in **Russian**. Use `ParseMode.HTML` for Telegram formatting.

### URL Validation

`utils.validate_and_sanitize_url()` enforces HTTPS-only, domain whitelist (`ra.co`, `dice.fm`), and rejects embedded credentials. Always use this for user-supplied URLs.

### Admin Commands

Admin-only commands (`/set`, `/unset`, `/status`, `/guestlist`, `/kick`) check `update.effective_user.id` against `BotConfiguration.admin_id`.

### Logging

Uses Python `logging` module with optional JSON output (controlled by `LOG_JSON_FORMAT` env var). The `JsonFormatter` class in `utils.py` outputs structured logs.
