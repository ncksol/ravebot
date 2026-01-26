# RaveBot 🎵

A Telegram bot for managing electronic music community events and group interactions. RaveBot helps coordinate event attendance, maintains a shared calendar, and manages new member introductions in Telegram groups.

## Features

- **Event Management**: Automatically create and track events from RA (Resident Advisor) and Dice.fm
- **Community Calendar**: Shared calendar integration with TeamUp for upcoming events
- **Member Management**: Automated welcome messages and member verification system
- **Event Announcements**: Scheduled updates of upcoming events in the group
- **Admin Tools**: Guest list management and moderation commands

## Architecture

The project consists of two main components:

- **Bot** (`apps/bot/`): Telegram bot handling user interactions and commands
- **Updater** (`apps/updater/`): Background service that syncs events from external calendars to the database

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- TeamUp Calendar API credentials
- (Optional) TimeTree API key for the updater service

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ncksol/ravebot.git
   cd ravebot
   ```

2. **Install dependencies**

   For the bot:
   ```bash
   cd apps/bot
   pip install -r requirements.txt
   ```

   For the updater:
   ```bash
   cd apps/updater
   pip install -r requirements.txt
   ```

   For development tools (linting, type checking):
   ```bash
   cd ../..  # back to root
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory or in each app directory:

   ```env
   # Database Configuration
   DATABASE_URL=postgresql://user:password@localhost:5432/ravebot

   # Bot Configuration
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_user_id

   # TeamUp Calendar Configuration
   TEAMUP_API_KEY=your_teamup_api_key
   TEAMUP_CALENDAR_KEY=your_calendar_key
   TEAMUP_CALENDAR_READER_KEY=your_reader_key
   TEAMUP_SUBCALENDAR_ID=your_subcalendar_id

   # RA (Resident Advisor) Configuration
   RA_QUERY_TEMPLATE_PATH=graphql_query_template.json

   # TimeTree Configuration (for updater service)
   TIMETREE_API_KEY=your_timetree_api_key
   ```

4. **Set up the database**

   The bot uses PostgreSQL. Ensure your database is running and the `DATABASE_URL` is correctly configured.

5. **Run the bot locally**
   ```bash
   cd apps/bot
   python main.py
   ```

6. **Run the updater service** (in a separate terminal)
   ```bash
   cd apps/updater
   python main.py
   ```

## Environment Variables

### Required for Bot

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `BOT_TOKEN` | Telegram Bot API token from BotFather |
| `ADMIN_ID` | Telegram user ID of the bot administrator |
| `TEAMUP_API_KEY` | TeamUp API key for calendar access |
| `TEAMUP_CALENDAR_KEY` | TeamUp calendar identifier |
| `TEAMUP_CALENDAR_READER_KEY` | TeamUp reader key for public calendar access |
| `TEAMUP_SUBCALENDAR_ID` | Specific subcalendar ID to use |
| `RA_QUERY_TEMPLATE_PATH` | Path to GraphQL query template file (default: `graphql_query_template.json`) |

### Required for Updater

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `TIMETREE_API_KEY` | TimeTree API key for fetching events |

## Deployment

The bot is designed to be deployed on [Fly.io](https://fly.io). Each component has its own `fly.toml` configuration.

### Deploy the Bot

```bash
cd apps/bot
fly deploy
```

### Deploy the Updater

```bash
cd apps/updater
fly deploy
```

### Environment Variables on Fly.io

Set secrets using the Fly CLI:

```bash
fly secrets set BOT_TOKEN=your_token_here
fly secrets set DATABASE_URL=your_database_url
fly secrets set ADMIN_ID=your_admin_id
# ... set other required secrets
```

## Bot Commands

### User Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help information and useful links |
| `/rave` | Display upcoming events for the week |
| `/calendar` | Get link to the shared calendar |
| `/createevent <url>` | Create a new event from RA.co or Dice.fm URL |
| `#whois` | Introduce yourself (required for new members) |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/set` | Enable automatic event updates (every hour) |
| `/unset` | Disable automatic event updates |
| `/update` | Manually update the pinned event announcement |
| `/guestlist @username` | Approve a user without requiring #whois |
| `/kick @username` | Remove a user from the group |

## Development

### Code Quality Tools

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **mypy**: Static type checker
- **pre-commit**: Git hooks for automated checks

### Setting Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

### Linting

```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Run type checking
mypy apps/bot apps/updater
```

### Code Style

- Maximum line length: 120 characters
- Use double quotes for strings
- Follow PEP 8 style guidelines
- Type hints are encouraged but not required

## Contributing

Contributions are welcome! Here's how to contribute:

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

4. **Run linters and formatters**
   ```bash
   ruff check --fix .
   ruff format .
   mypy apps/bot apps/updater
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add your meaningful commit message"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**

### Contribution Guidelines

- Write clear, descriptive commit messages
- Keep changes focused and atomic
- Test your changes locally before submitting
- Update the README if you add new features or change functionality
- Respect the existing code structure and conventions

## How It Works

### New Member Flow

1. User joins the Telegram group
2. Bot sends a welcome message explaining the introduction requirement
3. User has 90 minutes to post a message with `#whois` tag
4. If user doesn't respond within 90 minutes, they receive a warning
5. After 30 more minutes (2 hours total), user is automatically removed
6. Admin can use `/guestlist @username` to bypass this requirement

### Event Management

1. Admin posts event URL from RA.co or Dice.fm using `/createevent <url>`
2. Bot scrapes event details from the URL
3. Event is added to TeamUp calendar
4. Event appears in the weekly `/rave` announcement
5. Pinned announcement updates automatically every hour (if enabled with `/set`)

## License

[Add your license here]

## Support

For issues and questions, please [open an issue](https://github.com/ncksol/ravebot/issues) on GitHub.
