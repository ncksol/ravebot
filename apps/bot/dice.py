import urllib.request
import json
from bs4 import BeautifulSoup

from utils import logger, format_event_date
from models import Event


def get_dice_event_id(url) -> str:
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        
        logger.info(f"Retrieving the URL: {url}")

        response = urllib.request.urlopen(req)
        if response.status != 200:           
            logger.error(f"Failed to retrieve the URL. Status code: {response.status}")
            return None
        
        logger.info(f"URL retrieved successfully. Status code: {response.status}")

        html = response.read()
        soup = BeautifulSoup(html, 'html.parser')        

        meta_tag = soup.find('meta', attrs={'property': 'product:retailer_item_id'})
        if meta_tag:
            content = meta_tag.get('content')
            return content
        else:
            logger.error("No meta tag with property='product:retailer_item_id' found.")
            return None

    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def process_dice_event(url: str) -> Event:
    event_id = get_dice_event_id(url)
    if event_id is None:        
        return
    
    json = get_event_details(event_id)
    if json is None:        
        return
    
    event = Event(title=json['name'], url=url, description=json['description'], start_time=json['start_date'], end_time=json['end_date'], location=json['venue_address'])
    
    return event

def get_event_details(item_id: str) -> dict:
    url = f"https://api.dice.fm/events/{item_id}/ticket_types"
    response = urllib.request.urlopen(url)
    if response.status != 200:
        return {}
    data = json.loads(response.read())    
    description = data['about']['description']
    name = data['name']
    start_date = format_event_date(data['dates']['event_start_date'], '%Y-%m-%dT%H:%M:%S%z')
    end_date = format_event_date(data['dates']['event_end_date'], '%Y-%m-%dT%H:%M:%S%z')
    venue_address = data['venues'][0]['address']
    #event_venue_name = data['venues'][0]['name']
    event_details = {
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "name": name,
        "venue_address": venue_address
    }
    return event_details