import logging
import requests
import crud
import asyncio
from models import Event
from settings import TimeTreeConfiguration


_logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_events() -> "list[Event]":
    api_key = TimeTreeConfiguration.key
    api_url = 'https://timetreeapis.com/calendars/UT75VvR4kQ4t/upcoming_events?days=7'
    headers = {'Authorization': 'Bearer ' + api_key}
    r = requests.get(api_url, headers=headers)
    json = r.json()
    events = []
    for data in json['data']:
        event = Event(event_id=data['id'], title=data['attributes']['title'], start_time=data['attributes']['start_at'], end_time=data['attributes']['end_at'], 
                      location=data['attributes']['location'], url=data['attributes']['url'])
        events.append(event)
    return events

async def calendar_update():
    while True:
        events = get_events()
        crud.cleanup_events()
        for event in events:
            crud.upsert_event(event)
        _logger.info("Calendar updated")
        await asyncio.sleep(10*60)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(calendar_update())
    loop.run_forever()

