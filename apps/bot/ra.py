import requests, json, re, datetime, os

from models import Event
from settings import RAConfiguration

URL = 'https://ra.co/graphql'
HEADERS = {
    'Content-Type': 'application/json',
    'Referrer': 'https://ra.co/events/uk/london',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
}

#QUERY_TEMPLATE_PATH = "apps/bot/graphql_query_template.json"
#QUERY_TEMPLATE_PATH = "graphql_query_template.json"
#QUERY_TEMPLATE_PATH = os.getenv("GRAPHQL_QUERY_TEMPLATE_PATH")

def get_ra_event(id: str):
    with open(RAConfiguration.query_template_path, "r") as file:
            payload = json.load(file)

    payload["variables"]["id"] = id

    response = requests.post(URL, headers=HEADERS, json=payload)

    try:
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError):
        print(f"Error: {response.status_code}")
        return []

    if 'data' not in data:
        print(f"Error: {data}")
        return []
    
    return data["data"]["event"]


async def process_ra_event(url: str) -> Event:
    pattern = r'https://ra.co/events/(\d+)'
    match = re.match(pattern, url)
    if match is None:        
        return
    
    event_id = match.group(1)
    json = get_ra_event(event_id)
    if json is None:        
        return
    
    event = Event(title=json['title'], url=url, description=json['content'], start_time=json['startTime'], end_time=json['endTime'], location=json['venue']['name'])
    event.start_time = datetime.datetime.strptime(event.start_time, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S')
    event.end_time = datetime.datetime.strptime(event.end_time, '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S')
    
    return event