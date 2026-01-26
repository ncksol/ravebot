import os
from dotenv import dotenv_values

# Python Environment Variable setup required on System or .env file
config_env = {
    **dotenv_values(),  # load local file development variables
    **os.environ,  # override loaded values with system environment variables
}

# Determine environment (default to prod if not specified)
ENVIRONMENT = config_env.get("ENVIRONMENT", "prod")

class RAConfiguration:
    query_template_path = config_env["RA_QUERY_TEMPLATE_PATH"]

class BotConfiguration:
    # Use dev credentials if in dev environment, otherwise use prod
    if ENVIRONMENT == "dev":
        token = config_env.get("BOT_TOKEN_DEV") or config_env["BOT_TOKEN"]
    else:
        token = config_env["BOT_TOKEN"]
    admin_id = int(config_env["ADMIN_ID"])

class CalendarConfiguration:
    # Use dev credentials if in dev environment, otherwise use prod
    if ENVIRONMENT == "dev":
        api_key = config_env.get("TEAMUP_API_KEY_DEV") or config_env["TEAMUP_API_KEY"]
        calendar_key = config_env.get("TEAMUP_CALENDAR_KEY_DEV") or config_env["TEAMUP_CALENDAR_KEY"]
        calendar_reader_key = config_env["TEAMUP_CALENDAR_READER_KEY"]
        subcalendar_id = config_env["TEAMUP_SUBCALENDAR_ID"]
    else:
        api_key = config_env["TEAMUP_API_KEY"]
        calendar_key = config_env["TEAMUP_CALENDAR_KEY"]
        calendar_reader_key = config_env["TEAMUP_CALENDAR_READER_KEY"]
        subcalendar_id = config_env["TEAMUP_SUBCALENDAR_ID"]
    api_url = f"https://api.teamup.com/{calendar_key}"
    reader_url = f"https://teamup.com/{calendar_reader_key}"
    timezone = config_env.get("CALENDAR_TIMEZONE", "Europe/London")

class ErrorReportingConfiguration:
    sentry_dsn = config_env.get("SENTRY_DSN", None)
    environment = config_env.get("ENVIRONMENT", "development")

class LoggingConfiguration:
    json_format = config_env.get("LOG_JSON_FORMAT", "false").lower() == "true"
