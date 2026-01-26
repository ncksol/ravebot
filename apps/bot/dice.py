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

        response = urllib.request.urlopen(req, timeout=30)
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
        return None

async def process_dice_event(url: str) -> Event:
    event_id = get_dice_event_id(url)
    if event_id is None:        
        return
    
    event_data = get_event_details(event_id)
    if event_data is None:        
        return
    
    event = Event(title=event_data['name'], url=url, description=event_data['description'], start_time=event_data['start_date'], end_time=event_data['end_date'], location=event_data['venue_address'])
    
    return event

def get_event_details(item_id: str) -> dict:
    try:
        url = f"https://api.dice.fm/events/{item_id}/ticket_types"
        response = urllib.request.urlopen(url, timeout=30)
        if response.status != 200:
            logger.error(f"Failed to retrieve event details. Status code: {response.status}")
            return None
        data = json.loads(response.read())
        
        # Use .get() to safely access nested dictionary keys
        about = data.get('about', {})
        description = about.get('description', '')
        name = data.get('name', '')
        dates = data.get('dates', {})
        start_date = format_event_date(dates.get('event_start_date', ''), '%Y-%m-%dT%H:%M:%S%z')
        end_date = format_event_date(dates.get('event_end_date', ''), '%Y-%m-%dT%H:%M:%S%z')
        venues = data.get('venues', [])
        venue_address = venues[0].get('address', '') if venues else ''
        
        event_details = {
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "name": name,
            "venue_address": venue_address
        }
        return event_details
    except Exception as e:
        logger.error(f"Error retrieving event details: {e}")
        return None
