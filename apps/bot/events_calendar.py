import datetime
import requests
import urllib.parse

from utils import cut_string, logger
from models import Event
from settings import CalendarConfiguration

def get_events() -> "list[Event]":
    api_key = CalendarConfiguration.api_key
    headers = {'TeamUp-Token': api_key}

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())    
    api_url = f'{CalendarConfiguration.api_url}/events?startDate={today.strftime("%Y-%m-%d")}&endDate={(today + datetime.timedelta(6)).strftime("%Y-%m-%d")}'

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

def search_event(event: Event) -> str:
    api_key = CalendarConfiguration.api_key
    headers = {'TeamUp-Token': api_key, 'Content-Type': 'application/json'}

    params = {
        "startDate": datetime.datetime.strptime(event.start_time, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d"),
        "query": event.url
    }
    encoded_params = urllib.parse.urlencode(params)
    api_url = f'{CalendarConfiguration.api_url}/events?{encoded_params}'
    r = requests.get(api_url, headers=headers)
    if r.status_code != 200:
        logger.error(f"Failed to search event: {r.text}")
        return None
    
    json = r.json()
    events = []    
    for data in json['events']:
        event = Event(event_id=data['id'], title=data['title'], start_time=data['start_dt'], end_time=data['end_dt'], 
                      location=data['location'], url=data['custom']['url'], description=data['notes'])
        events.append(event)

    if len(events) == 0:
        logger.warning("No events found")
        return None
    return  f'{CalendarConfiguration.reader_url}/events/{events[0].event_id}'


def create_calendar_event(event: Event) -> bool:    
    api_key = CalendarConfiguration.api_key
    headers = {'TeamUp-Token': api_key, 'Content-Type': 'application/json'}

    api_url = f'{CalendarConfiguration.api_url}/events'

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

def extract_first_8_words(s):
    # Split the string into words
    words = s.split()

    # Take the first 8 words
    first_8_words = words[:8]

    # Join the words back into a string
    return ' '.join(first_8_words)