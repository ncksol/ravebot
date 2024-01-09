import datetime
import requests

from utils import cut_string, logger
from models import Event
from settings import CalendarConfiguration

def get_events() -> "list[Event]":
    api_key = CalendarConfiguration.api_key
    headers = {'TeamUp-Token': api_key}

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())    
    api_url = f'{CalendarConfiguration.url}/events?startDate={today.strftime("%Y-%m-%d")}&endDate={(today + datetime.timedelta(6)).strftime("%Y-%m-%d")}'

    r = requests.get(api_url, headers=headers)
    json = r.json()
    events = []    
    for data in json['events']:
        event = Event(event_id=data['id'], title=data['title'], start_time=data['start_dt'], end_time=data['end_dt'], 
                      location=data['location'], url=data['custom']['url'], description=data['notes'])
        events.append(event)
    
    if len(events) == 0:
        logger.warning("No events found")
    return events

def create_calendar_event(event: Event) -> bool:    
    api_key = CalendarConfiguration.api_key
    headers = {'TeamUp-Token': api_key, 'Content-Type': 'application/json'}

    api_url = f'{CalendarConfiguration.url}/events'

    payload = {
        "subcalendar_ids": [
            CalendarConfiguration.subcalendar_id
        ],
        "start_dt": f"{event.start_time}",
        "end_dt": f"{event.end_time}",
        "tz" : "Europe/London",
        "notes": f"{cut_string(event.description, 65535)}",
        "title": f"{cut_string(event.title, 255)}",
        "location": f"{cut_string(event.location, 255)}",
        "custom": {
            "url": f"{event.url}"
        }
    }

    r = requests.post(api_url, headers=headers, json=payload)
    if r.status_code != 201:
        logger.error(f"Failed to create event: {r.text}")
        return False
    return True