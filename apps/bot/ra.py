import requests, json, re, datetime

from models import Event
from settings import RAConfiguration
from utils import logger

URL = 'https://ra.co/graphql'
HEADERS = {
    'Content-Type': 'application/json',
    'Referrer': 'https://ra.co/events/uk/london',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
}

def get_ra_event(id: str):
    try:
        with open(RAConfiguration.query_template_path, "r") as file:
            payload = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading query template: {e}")
        return None

    payload["variables"]["id"] = id

    try:
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching RA event: {e}")
        return None
    except ValueError as e:
        logger.error(f"Error parsing response JSON: {e}")
        return None

    if 'data' not in data:
        logger.error(f"Error: Missing 'data' in response: {data}")
        return None
    
    return data["data"].get("event")


async def process_ra_event(url: str) -> Event:
    pattern = r'https://ra.co/events/(\d+)'
    match = re.match(pattern, url)
    if match is None:        
        return
    
    event_id = match.group(1)
    event_data = get_ra_event(event_id)
    if event_data is None:        
        return
    
    try:
        venue = event_data.get('venue', {})
        location = venue.get('name', '') if venue else ''
        start_time = event_data.get('startTime', '')
        end_time = event_data.get('endTime', '')
        
        if not start_time or not end_time:
            logger.error("Missing start_time or end_time in RA event data")
            return None
            
        event = Event(
            title=event_data.get('title', ''), 
            url=url, 
            description=event_data.get('content', ''), 
            start_time=start_time, 
            end_time=end_time, 
            location=location
        )
        event.start_time = datetime.datetime.strptime(event.start_time, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S')
        event.end_time = datetime.datetime.strptime(event.end_time, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S')
    except (ValueError, KeyError) as e:
        logger.error(f"Error processing RA event data: {e}")
        return None
    
    return event
