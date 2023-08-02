import logging
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, PicklePersistence, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.constants import MessageEntityType
import datetime
import requests
import json
import re
from models import Event, Cache
from settings import BotConfiguration, TimeTreeConfiguration

_logger = logging.getLogger(__name__)
_welcome_message = "Привет {name}. Добро пожаловать в нашу группу. Тут мы обсуждаем разную электронную музыку, делимся интересным треками и организовываем совместные походы на ивенты. Мы стараемся создавать атмосферу теплой домашней тусовки, а поэтому хорошо было бы чтобы окружающие хотя бы немного знали друг о друге. Посему расскажи пожалуйста немного о себе - кто ты, откуда, чем занимаешься, что (или кто) привело тебя к нам в группу и самое главное какие стили электронной музыки тебе наиболее близки (три самых любимых диджея?).\n\rА чтобы узнать побольше о группе и ее участниках кликай сюда, там вся полезная информация - https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3.\n\r\n\r<b>Для того чтобы представиться напиши сообщение в чат c тегом #whois. Если этого не сделать в течении пары часов, то злобный бот тебя кикнет.</b>"

URL = 'https://ra.co/graphql'
HEADERS = {
    'Content-Type': 'application/json',
    'Referrer': 'https://ra.co/events/uk/london',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
}
QUERY_TEMPLATE_PATH = "graphql_query_template.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_ra_event(id: str):
    with open(QUERY_TEMPLATE_PATH, "r") as file:
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

def cut_string(string: str, length: int):
    if len(string) > length:
        string = string[:length-3] + "..."
    return string

def get_events() -> "list[Event]":
    api_key = TimeTreeConfiguration.key
    api_url = 'https://timetreeapis.com/calendars/UT75VvR4kQ4t/upcoming_events?days=7'
    headers = {'Authorization': 'Bearer ' + api_key}
    r = requests.get(api_url, headers=headers)
    json = r.json()
    events = []
    for data in json['data']:
        event = Event(event_id=data['id'], title=data['attributes']['title'], start_time=data['attributes']['start_at'], end_time=data['attributes']['end_at'], 
                      location=data['attributes']['location'], url=data['attributes']['url'], description=data['attributes']['description'])
        events.append(event)
    return events

def create_calendar_event(event: Event) -> bool:    
    api_key = TimeTreeConfiguration.key
    api_url = 'https://timetreeapis.com/calendars/UT75VvR4kQ4t/events'
    headers = {'Authorization': 'Bearer ' + api_key + '', 'Accept': 'application/vnd.timetree.v1+json', 'Content-Type': 'application/json'}

    payload = {
        "data": {
        "attributes": {
            "category": "schedule",
            "title": f"{cut_string(event.title, 50)}",
            "all_day": False,
            "start_at": f"{event.start_time}",
            "start_timezone": "Europe/London",
            "end_at": f"{event.end_time}",
            "end_timezone": "Europe/London",
            "description": f"{cut_string(event.description, 1000)}",
            "location": f"{cut_string(event.location, 100)}",
            "url": f"{event.url}",
        },
        "relationships": {
            "label": {
            "data": {
                "id": "UT75VvR4kQ4t,9",
                "type": "label"
            }
            }
        }
    }
    }

    r = requests.post(api_url, headers=headers, json=payload)
    if r.status_code != 201:
        _logger.error(f"Failed to create event: {r.text}")
        return False
    return True

def get_rave_message(context: ContextTypes.DEFAULT_TYPE):
    cache = context.chat_data.get('cache', Cache(datetime.datetime.now(), []))    
    if not cache.events or len(cache.events) == 0 or (datetime.datetime.now().date() - cache.last_update.date()).days >= 1:
        update_cache(context)

    message = '<u>Upcoming events:</u>\n\n'
    for event in cache.events:
        message += str(event) + '\n'
    return message

def update_cache(context: ContextTypes.DEFAULT_TYPE):
    events = get_events()
    cache = context.chat_data.get('cache', Cache(datetime.datetime.now(), []))    
    cache.update(events)
    context.chat_data['cache'] = cache
    _logger.info("Cache updated")

async def rave(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    message = get_rave_message(context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    update_cache(context)
    await update_announcement(context, update.effective_chat.id)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Вот ссылка на полезную информацию про группу: https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3")

async def bot_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.effective_message.new_chat_members:
        if member.is_bot:
            return
        
        context.user_data['new_member'] = True
        name = get_name(member.first_name, member.last_name)
        mention = get_mention(member.id, name)

        message = _welcome_message.format(name=mention)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

        remove_job_if_exists(str(member.id), context)
        context.job_queue.run_once(warn_idle, when=90*60, chat_id=update.effective_chat.id, user_id=member.id, name=str(member.id))
        context.chat_data[str(member.id)] = name

async def warn_idle(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    username = context.chat_data.get(str(user_id), None)
    mention = get_mention(user_id, username)

    await context.bot.send_message(chat_id=context.job.chat_id, text=f"{mention} все ещё не представились. У тебя есть еще полчаса прежде чем мы распрощаемся.", parse_mode=ParseMode.HTML)    
    context.job_queue.run_once(kick_idle, when=30*60, chat_id=update.effective_chat.id, user_id=user_id, name=str(user_id))

async def kick_idle(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    username = context.chat_data.pop(str(user_id), None)
    mention = get_mention(user_id, username)

    await context.bot.send_message(chat_id=context.job.chat_id, text=f"{mention} не представились и покидают чат.", parse_mode=ParseMode.HTML)
    await context.bot.ban_chat_member(chat_id=context.job.chat_id, user_id=context.job.user_id)
    await context.bot.unban_chat_member(chat_id=context.job.chat_id, user_id=context.job.user_id, only_if_banned=True)

async def whois(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_new_member = context.user_data.pop('new_member', False)
    if is_new_member == False:
        return
    
    member_id = context._user_id

    success = remove_job_if_exists(str(member_id), context)
    if success:
        mention = get_mention(member_id, get_name(update.effective_user.first_name, update.effective_user.last_name))
        await update.effective_message.reply_html(f"Спасибо {mention}! Очень приятно познакомиться.")

def get_name(first_name: str, last_name: str) -> str:
    if last_name is not None:
        return f"{first_name} {last_name}"
    return first_name

def get_mention(user_id: int, name: str) -> str:
    return f"<a href='tg://user?id={str(user_id)}'>{name}</a>"

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
    
    message = get_rave_message(context)
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
    job_removed = remove_job_if_exists(f"update_{chat_id}", context)
    #context.job_queue.run_daily(update_announcement_timer, time=datetime.time(hour=0, minute=5, second=0), chat_id=chat_id, name=str(chat_id))    
    context.job_queue.run_repeating(update_announcement_timer, interval=1*60*60, first=60, chat_id=chat_id, name=str(chat_id))
    
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
    job_removed = remove_job_if_exists(f"update_{chat_id}", context)
    text = "Update timer successfully removed!" if job_removed else "You have no active update timer."
    await update.effective_message.reply_text(text)

async def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mentions = update.effective_message.parse_entities(MessageEntityType.URL)
    url = next(iter(mentions.values()))

    if url is None:
        await update.effective_message.reply_text("No event URL found.")
        return
    
    pattern = r'https://ra.co/events/(\d+)'
    match = re.match(pattern, url)
    if match is None:
        await update.effective_message.reply_text("Invalid event URL. Accepted format: https://ra.co/events/1234567")
        return
    
    event_id = match.group(1)
    json = get_ra_event(event_id)
    if json is None:
        await update.effective_message.reply_text("Invalid event URL.")
        return
    
    event = Event(title=json['title'], url=url, description=json['content'], start_time=json['startTime'], end_time=json['endTime'], location=json['venue']['name'])
    created = create_calendar_event(event)
    if created:
        await update.effective_message.reply_text("Event successfully created!")
    else:
        await update.effective_message.reply_text("Failed to create event.")


if __name__ == '__main__':
    persistence = PicklePersistence('bot_data')
    application = ApplicationBuilder().token(BotConfiguration.token).persistence(persistence).build()
    
    rave_handler = CommandHandler('rave', rave)
    application.add_handler(rave_handler)

    update_hander = CommandHandler('update', update)
    application.add_handler(update_hander)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    set_handler = CommandHandler('set', set)
    application.add_handler(set_handler)

    unset_handler = CommandHandler('unset', unset)
    application.add_handler(unset_handler)

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_welcome))    
    
    whois_handler = MessageHandler(filters.Regex(r'(^|\s+)#whois($|\s+)'), whois)
    application.add_handler(whois_handler)

    create_event_handler = CommandHandler('createevent', create_event)
    application.add_handler(create_event_handler)

    application.run_polling()