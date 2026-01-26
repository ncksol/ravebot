# ravebot

A Telegram bot for managing electronic music community groups.

## Features

- New member welcome and verification system
- Event creation from ra.co and dice.fm
- Calendar integration with Teamup
- Admin commands for managing members
- Multi-language support (Russian and English)

## Configuration

The bot is configured via environment variables. Create a `.env` file or set these in your environment:

### Required Variables

- `BOT_TOKEN` - Your Telegram bot token
- `DATABASE_URL` - PostgreSQL database connection string
- `RA_QUERY_TEMPLATE_PATH` - Path to GraphQL query template file
- `TEAMUP_API_KEY` - Teamup API key
- `TEAMUP_CALENDAR_KEY` - Teamup calendar key
- `TEAMUP_CALENDAR_READER_KEY` - Teamup calendar reader key
- `TEAMUP_SUBCALENDAR_ID` - Teamup subcalendar ID

### Admin Configuration

You can configure bot administrators in two ways:

**Option 1: Single Admin (Legacy)**
```
ADMIN_ID=123456789
```

**Option 2: Multiple Admins (Recommended)**
```
ADMIN_IDS=123456789,987654321,456789123
```

Multiple admin IDs should be comma-separated. Any user in this list will have admin privileges.

### Language Configuration

Set the bot language using the `LANGUAGE` environment variable:

```
LANGUAGE=en  # English
LANGUAGE=ru  # Russian (default)
```

Supported languages:
- `ru` - Russian (default)
- `en` - English

## Admin Commands

The following commands are restricted to admin users:

- `/set` - Set up automatic event announcements
- `/unset` - Remove automatic event announcements
- `/guestlist @username` - Manually approve a new member
- `/kick @username` - Kick a user from the group

## User Commands

- `/rave` - Show upcoming events
- `/update` - Update the pinned events announcement
- `/help` - Show help information
- `/calendar` - Get calendar link
- `/createevent [url]` - Create an event from ra.co or dice.fm URL