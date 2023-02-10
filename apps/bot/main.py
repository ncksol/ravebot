import logging
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, PicklePersistence
from telegram.constants import ParseMode
import datetime
import requests
from models import Event, Cache
from settings import BotConfiguration, TimeTreeConfiguration

_logger = logging.getLogger(__name__)

cache = Cache(datetime.datetime.now(), [])

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

def get_rave_message():
    message = '<u>Upcoming events:</u>\n\n'
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
    #message = get_rave_message()
    #await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)    
    await update_announcement(context, update.effective_chat.id)

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def update_announcement_timer(context: ContextTypes.DEFAULT_TYPE):
    _logger.info("Running scheduled announcement update...")
    job = context.job
    await update_announcement(context, job.chat_id)

async def update_announcement(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    announcement_id = None
    if 'announcement_id' in context.chat_data and context.chat_data["announcement_id"] is not None:
        announcement_id = int(context.chat_data["announcement_id"])
    
    message = get_rave_message()
    msg_object = None
    if announcement_id is not None:
        try:
            _logger.info("Announcement message found. Updating...")
            msg_object = await context.bot.edit_message_text(chat_id=chat_id, message_id=announcement_id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)        
        except BadRequest as e:
            if e.message == "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                _logger.info("Nothing changed. Quitting...")
                return            
                
    if msg_object is None or announcement_id is None:
        _logger.info("Announcement message not found. Creating new one...")
        msg_object = await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    
    if msg_object is not None:
        await msg_object.pin(disable_notification=True)
        context.chat_data["announcement_id"] = msg_object.message_id
            
async def set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text("Sorry, you are not allowed to use this command.")
        return

    chat_id = update.effective_message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_daily(update_announcement_timer, time=datetime.time(hour=0, minute=5, second=0), chat_id=chat_id, name=str(chat_id))
    #context.job_queue.run_repeating(update_announcement, interval=60, chat_id=chat_id, name=str(chat_id))
    
    text = "Update timer successfully set!"
    if job_removed:
        text += " Old one was removed."
    await update.effective_message.reply_text(text)

async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text("Sorry, you are not allowed to use this command.")
        return
    
    chat_id = update.effective_message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Update timer successfully removed!" if job_removed else "You have no active update timer."
    await update.effective_message.reply_text(text)    

if __name__ == '__main__':

    events = get_events()
    cache.update(events)

    persistence = PicklePersistence('bot_data')
    application = ApplicationBuilder().token(BotConfiguration.token).persistence(persistence).build()
    
    rave_handler = CommandHandler('rave', rave)
    application.add_handler(rave_handler)

    update_hander = CommandHandler('update', update)
    application.add_handler(update_hander)

    set_handler = CommandHandler('set', set)
    application.add_handler(set_handler)

    unset_handler = CommandHandler('unset', unset)
    application.add_handler(unset_handler)
    
    application.run_polling()