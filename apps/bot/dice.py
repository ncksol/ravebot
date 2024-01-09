import requests
from bs4 import BeautifulSoup

from utils import logger
from models import Event


def get_dice_event_id(url) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:            
            soup = BeautifulSoup(response.text, 'html.parser')

            meta_tag = soup.find('meta', attrs={'property': 'product:retailer_item_id'})
            if meta_tag:
                content = meta_tag.get('content')
                return content
            else:
                logger.error("No meta tag with property='product:retailer_item_id' found.")
                return None
        else:
            logger.error(f"Failed to retrieve the URL. Status code: {response.status_code}")
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
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    data = response.json()
    description = data['about']['description']
    name = data['name']
    start_date = data['dates']['event_start_date']
    end_date = data['dates']['event_end_date']
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