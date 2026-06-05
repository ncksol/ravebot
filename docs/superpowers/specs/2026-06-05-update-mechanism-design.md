# Robust Telegram Announcement Update Mechanism Design

## Context

Ravebot should keep a pinned Telegram chat message updated with the latest weekly events. The current production bot only schedules automatic updates when an admin runs `/set`, then stores that timer flag in local `bot_data` pickle state. Production inspection showed the live container still had chat/cache state, but `bot_data["update_timers"]` was empty, so no hourly announcement job was being restored or run.

The fix should make the production updater independent of volatile container-local timer state.

## Goals

- Schedule the production pinned-announcement updater from durable deployment configuration.
- Recover automatically when the stored pinned message ID is missing, stale, deleted, or no longer editable.
- Preserve the existing cache behavior that keeps the last good event list when Teamup fails.
- Improve operational visibility so `/status` shows whether the configured announcement job is healthy.
- Keep the change focused; do not add a database or external scheduler.

## Non-goals

- Replacing Telegram long polling with webhooks.
- Adding a new HTTP API surface for external schedulers.
- Persisting bot state to a database.
- Supporting multiple production announcement chats in the first implementation.

## Recommended approach

Use environment configuration as the source of truth for the production announcement job.

Add a required production setting:

- `ANNOUNCEMENT_CHAT_ID`: Telegram chat ID whose pinned weekly events message should be managed.

Add optional settings with safe defaults:

- `ANNOUNCEMENT_INTERVAL_SECONDS`: defaults to `3600`.
- `ANNOUNCEMENT_FIRST_RUN_SECONDS`: defaults to `60`.

On startup, if `ANNOUNCEMENT_CHAT_ID` is configured, the bot registers one repeating update job for that chat. Registration is idempotent: before adding the job, remove any existing job with the configured job name. This prevents duplicate jobs after restarts or repeated initialization.

## Components

### Configuration

Extend `settings.py` with an announcement configuration section that reads the new environment variables and converts them to typed values. Missing `ANNOUNCEMENT_CHAT_ID` should mean no configured production updater in local/dev contexts, but production deployment should provide it.

### Startup scheduler

Extract startup job registration into a small helper, for example `register_configured_announcement_job(application)`. The helper should:

1. Check whether `ANNOUNCEMENT_CHAT_ID` is configured.
2. Remove any existing job with the configured announcement job name.
3. Register `update_announcement_timer` with the configured interval, first-run delay, chat ID, and stable job name.
4. Log whether the configured updater was registered or skipped.

This helper should run from `post_init` and should be the production source of truth. Existing `/set` and `/unset` commands may remain for manual/ad-hoc timers, but they should not be required for the configured production chat. `/unset` should not permanently disable the configured production job; removing that job should require changing deployment configuration.

### Announcement update flow

Keep `announcement_id` in `context.chat_data` as an optimization. The normal path remains:

1. Build the weekly events message with `get_rave_message()`.
2. If `announcement_id` exists, try to edit that message.
3. If editing succeeds and the message changed, keep the existing pinned message.
4. If Telegram says the message is not modified, treat that as success.

For recoverable Telegram edit failures, create and pin a new announcement message:

- Message not found.
- Message cannot be edited.
- Message to edit not found.
- Any similar `BadRequest` that indicates the stored message ID is stale.

After successfully pinning a new message, save the new `announcement_id` and best-effort cleanup the old one. Cleanup failures should be logged but should not fail the update.

### Cache and calendar behavior

Keep the current distinction between Teamup API failure and a valid empty calendar response:

- `get_events() is None`: API failure; keep the existing cache and log the failure.
- `get_events() == []`: valid empty result; update the cache so the announcement can show the no-events message.

This prevents transient Teamup failures from erasing a good pinned announcement.

### Status and observability

Enhance `/status` for admins with announcement-specific fields:

- Whether `ANNOUNCEMENT_CHAT_ID` is configured.
- Whether the configured announcement job is currently scheduled.
- Cache event count and cache age.
- Whether an `announcement_id` is stored for the current chat.
- Last announcement update attempt status, tracked in bot or chat data with timestamp, outcome, and a short non-secret reason.

The logger should emit warnings for recoverable Telegram failures and errors for unexpected failures. The log level configuration can remain unchanged, but warning/error events must carry enough context to diagnose missed updates without exposing secrets.

## Data flow

```text
Container starts
  -> settings load ANNOUNCEMENT_CHAT_ID
  -> post_init registers configured hourly update job
  -> job fires after ANNOUNCEMENT_FIRST_RUN_SECONDS
  -> update_announcement_timer calls update_announcement(chat_id)
  -> get_rave_message refreshes cache if needed
  -> edit stored announcement_id if possible
  -> otherwise create, pin, store new announcement_id
```

## Error handling

- Missing `ANNOUNCEMENT_CHAT_ID`: skip configured startup scheduling and log a warning in production.
- Duplicate scheduled job: remove existing job before registering the configured job.
- Teamup API failure: keep the existing cache and log a warning.
- Empty Teamup response: update cache to an empty event list and announce no upcoming events.
- Telegram edit stale-message failure: create and pin a new announcement.
- Telegram create/pin failure: log an error and leave existing state unchanged.
- Old-message cleanup failure: log a warning and continue.

## Testing

Add focused unit tests for:

- Configured startup job registration when `ANNOUNCEMENT_CHAT_ID` is present.
- Startup skipping registration when `ANNOUNCEMENT_CHAT_ID` is absent.
- Idempotent registration removing an existing configured job before scheduling a new one.
- `update_announcement()` editing the stored announcement message when valid.
- `update_announcement()` treating "Message is not modified" as success.
- `update_announcement()` creating and pinning a new message when the stored message ID is stale.
- Cache preservation when `get_events()` returns `None`.
- Cache update to empty list when `get_events()` returns `[]`.

Run the existing local validation path after implementation:

```bash
cd apps/bot
pytest -v --tb=short
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
python -m black --check --diff .
```

## Deployment

Add `ANNOUNCEMENT_CHAT_ID` to the Azure Container App environment configuration. The current GitHub Actions deploy step reuses the target Container App and deploys a new image, so the environment setting should be configured on the Container App resource and preserved across image deployments.

After deployment:

1. Confirm `/status` reports the configured announcement job as active.
2. Run `/update` once in the Telegram chat to refresh immediately.
3. Confirm the next scheduled run does not require `/set`.

## Open decisions

The design intentionally targets one production announcement chat. If multiple chat support becomes necessary later, the same pattern can be extended with a comma-separated `ANNOUNCEMENT_CHAT_IDS` setting or a durable external state store.
