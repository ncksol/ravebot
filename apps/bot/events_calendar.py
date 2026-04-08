import datetime
import requests
import urllib.parse
from dateutil import parser

from utils import cut_string, logger
from models import Event
from settings import CalendarConfiguration


def _parse_event(data: dict) -> Event:
    """Parse a Teamup API event dict into an Event model."""
    start_dt = data.get("start_dt", "")
    end_dt = data.get("end_dt", "")
    if not start_dt or not end_dt:
        raise ValueError("Missing start_dt or end_dt in event data")
    start_time = (
        parser.parse(start_dt).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
    )
    end_time = parser.parse(end_dt).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
    custom_data = data.get("custom", {})
    url = custom_data.get("url", "")
    return Event(
        event_id=data.get("id", ""),
        title=data.get("title", ""),
        start_time=start_time,
        end_time=end_time,
        location=data.get("location", ""),
        url=url,
        description=data.get("notes", ""),
    )


def get_events() -> "list[Event] | None":
    """Fetch this week's events. Returns None on API failure, [] if no events."""
    api_key = CalendarConfiguration.api_key
    headers = {"TeamUp-Token": api_key}

    today = datetime.date.today()
    api_url = f'{CalendarConfiguration.api_url}/events?startDate={today.strftime("%Y-%m-%d")}&endDate={(today + datetime.timedelta(6)).strftime("%Y-%m-%d")}'

    try:
        r = requests.get(api_url, headers=headers, timeout=30)
        r.raise_for_status()
        response_data = r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch events from calendar API: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse JSON response from calendar API: {e}")
        return None

    events = []
    for data in response_data.get("events", []):
        try:
            events.append(_parse_event(data))
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse event data: {e}")
            continue

    return events


def search_event(event: Event) -> str:
    api_key = CalendarConfiguration.api_key
    headers = {"TeamUp-Token": api_key, "Content-Type": "application/json"}

    params = {
        "startDate": datetime.datetime.strptime(
            event.start_time, "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y-%m-%d"),
        "query": f'"{event.url}"',
    }
    encoded_params = urllib.parse.urlencode(params)
    api_url = f"{CalendarConfiguration.api_url}/events?{encoded_params}"
    try:
        r = requests.get(api_url, headers=headers, timeout=30)
        r.raise_for_status()
        response_data = r.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to search event: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None

    events = []
    for data in response_data.get("events", []):
        try:
            events.append(_parse_event(data))
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse event data in search: {e}")
            continue

    if not events:
        logger.warning("No events found")
        return None
    return f"{CalendarConfiguration.reader_url}/events/{events[0].event_id}"


def create_calendar_event(event: Event) -> bool:
    api_key = CalendarConfiguration.api_key
    headers = {"TeamUp-Token": api_key, "Content-Type": "application/json"}

    api_url = f"{CalendarConfiguration.api_url}/events"

    payload = {
        "subcalendar_ids": [CalendarConfiguration.subcalendar_id],
        "start_dt": f"{event.start_time}",
        "end_dt": f"{event.end_time}",
        "tz": CalendarConfiguration.timezone,
        "notes": f"{cut_string(event.description, 65535)}",
        "title": f"{cut_string(event.title, 255)}",
        "location": f"{cut_string(event.location, 255)}",
        "custom": {"url": f"{event.url}"},
    }

    try:
        r = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if r.status_code != 201:
            logger.error(f"Failed to create event: {r.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create event (network error): {e}")
        return False


def get_calendar_link():
    return CalendarConfiguration.reader_url
