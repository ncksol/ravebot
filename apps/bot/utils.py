import logging, datetime, sys

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

def cut_string(string: str, length: int):
    if len(string) > length:
        string = string[:length-3] + "..."
    return string

def get_name(first_name: str, last_name: str) -> str:
    if last_name is not None:
        return f"{first_name} {last_name}"
    return first_name

def get_mention(user_id: int, name: str) -> str:
    return f"<a href='tg://user?id={str(user_id)}'>{name}</a>"

def format_event_date(date: str, format: str) -> str:
    return datetime.datetime.strptime(date, format).strftime('%Y-%m-%dT%H:%M:%S')