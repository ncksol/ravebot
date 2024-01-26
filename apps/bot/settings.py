import os
from dotenv import dotenv_values

# Python Environment Variable setup required on System or .env file
config_env = {
    **dotenv_values(),  # load local file development variables
    **os.environ,  # override loaded values with system environment variables
}

class DatabaseConfiguration:
    connection_string = config_env["DATABASE_URL"]

class RAConfiguration:
    query_template_path = config_env["RA_QUERY_TEMPLATE_PATH"]

class BotConfiguration:
    token = config_env["BOT_TOKEN"]
    admin_id = int(config_env["ADMIN_ID"])

class CalendarConfiguration:        
    api_key = config_env["TEAMUP_API_KEY"]
    calendar_key = config_env["TEAMUP_CALENDAR_KEY"]
    calendar_reader_key = config_env["TEAMUP_CALENDAR_READER_KEY"]
    subcalendar_id = config_env["TEAMUP_SUBCALENDAR_ID"]
    api_url = f"https://api.teamup.com/{calendar_key}"
    reader_url = f"https://teamup.com/{calendar_reader_key}"