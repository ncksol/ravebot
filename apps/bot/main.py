import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.constants import ParseMode
import os
import requests
import datetime
from models import Event, Cache
from dotenv import dotenv_values

config_env = {
    **dotenv_values(),
    **os.environ,
}

_logger = logging.getLogger(__name__)

cache = Cache(datetime.datetime.now(), [])

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_events():
    api_key = config_env['TIMETREE_API_KEY']
    api_url = 'https://timetreeapis.com/calendars/UT75VvR4kQ4t/upcoming_events?days=7'
    headers = {'Authorization': 'Bearer ' + api_key}
    r = requests.get(api_url, headers=headers)
    json = r.json()
    events = []
    for data in json['data']:
        event = Event(data['attributes']['title'], data['attributes']['start_at'], data['attributes']['end_at'], data['attributes']['location'], data['attributes']['url'])
        events.append(event)    
    return events

def get_rave_message():
    message = '<u>Пати на этой неделе:</u>\n\n'
    for event in cache.events:
        message += str(event) + '\n'
    return message

def update_cache():
    events = get_events()
    cache.update(events)
    _logger.info("Cache updated")

async def rave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not cache.events or (datetime.datetime.now().date() - cache.last_update.date()).days >= 1:
        update_cache()
    message = get_rave_message()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_cache()
    message = get_rave_message()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)    

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get('time') == None:
        a = 0
    else:
        a = context.chat_data.get('time')
        a += 1
    
    context.chat_data['time'] = a
    await context.bot.send_message(chat_id=update.effective_chat.id, text='current value: ' + str(a))

if __name__ == '__main__':
    events = get_events()
    cache.update(events)

    application = ApplicationBuilder().token(config_env['BOT_TOKEN']).build()
    
    rave_handler = CommandHandler('rave', rave)
    application.add_handler(rave_handler)

    update_hander = CommandHandler('update', update)
    application.add_handler(update_hander)

    test_handler = CommandHandler('test', test)
    application.add_handler(test_handler)
    
    application.run_polling()