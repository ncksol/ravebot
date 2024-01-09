import datetime

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, PicklePersistence, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.constants import MessageEntityType
from urllib.parse import urlparse

from ra import process_ra_event
from dice import process_dice_event
from models import Cache
from settings import BotConfiguration
from events_calendar import get_events, create_calendar_event
from utils import get_name, get_mention, logger
from text import welcome_message, success_message, help_message, warn_message, kick_message, no_event_url_message, unsupported_event_url_message, event_created_message, event_creation_error_message, admin_access_error_message, queue_user_not_found_message, guest_list_success_message, kick_message, upcoming_events_header, no_upcoming_events_message

async def rave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    message = get_rave_message(context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    update_cache(context)
    await update_announcement(context, update.effective_chat.id)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)

async def new_member_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.effective_message.new_chat_members:
        if member.is_bot:
            return
        
        context.user_data['new_member'] = True
        name = get_name(member.first_name, member.last_name)
        mention = get_mention(member.id, name)

        message = welcome_message.format(name=mention)

        welcome_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

        context.chat_data['welcome_' + str(member.id)] = welcome_msg.message_id

        remove_job_if_exists(str(member.id), context)
        context.job_queue.run_once(warn_idle, when=90*60, chat_id=update.effective_chat.id, user_id=member.id, name=str(member.id))
        context.chat_data[str(member.id)] = name
        context.chat_data[f'@{member.username}'] = member.id

async def whois_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_new_member = context.user_data.pop('new_member', False)
    if is_new_member == False:
        return
    
    member_id = context._user_id

    success = remove_job_if_exists(str(member_id), context)
    if success:
        mention = get_mention(member_id, get_name(update.effective_user.first_name, update.effective_user.last_name))
        message = success_message.format(name=mention)
        await update.effective_message.reply_html(message)

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text(admin_access_error_message)
        return

    chat_id = update.effective_message.chat_id
    job_removed = remove_job_if_exists(f"update_{chat_id}", context)    
    context.job_queue.run_repeating(update_announcement_timer, interval=1*60*60, first=60, chat_id=chat_id, name=str(chat_id))
    
    text = "Update timer successfully set!"
    if job_removed:
        text += " Old one was removed."
    await update.effective_message.reply_text(text)

async def unset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text(admin_access_error_message)
        return
    
    chat_id = update.effective_message.chat_id
    job_removed = remove_job_if_exists(f"update_{chat_id}", context)
    text = "Update timer successfully removed!" if job_removed else "You have no active update timer."
    await update.effective_message.reply_text(text)

async def create_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mentions = update.effective_message.parse_entities(MessageEntityType.URL)
    if len(list(mentions.values())) == 0:
        await update.effective_message.reply_text(no_event_url_message)
        return
    
    url = next(iter(mentions.values()))

    if url is None:
        await update.effective_message.reply_text(no_event_url_message)
        return
    
    event = None
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain == "ra.co":
        event = await process_ra_event(url)        
    elif domain == "dice.fm":
        event = await process_dice_event(url)
    else:
        await update.effective_message.reply_text(unsupported_event_url_message)
        return
    
    if event is None:
        await update.effective_message.reply_text(event_creation_error_message)
        return
            
    created = create_calendar_event(event)
    if created:
        await update.effective_message.reply_text(event_created_message)
        update_cache(context)
    else:
        await update.effective_message.reply_text(event_creation_error_message)


async def guest_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text(admin_access_error_message)
        return

    mentions = update.effective_message.parse_entities(MessageEntityType.MENTION)    
    username = list(mentions.values())[0]
    user_id = context.chat_data.get(username, None)
    if user_id is None:
        await update.effective_message.reply_text(queue_user_not_found_message)
        return
        
    mention = get_mention(user_id, username)
    success = remove_job_if_exists(str(user_id), context)
    if success:
        await update.effective_message.reply_html(guest_list_success_message.format(name=mention))
        await clean_up_welcome_message(context, update.effective_chat.id, user_id)
        await clean_up_warn_message(context, update.effective_chat.id, user_id)
            
        message = success_message.format(name=mention)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != BotConfiguration.admin_id:
        await update.effective_message.reply_text(admin_access_error_message)
        return

    mentions = update.effective_message.parse_entities(MessageEntityType.MENTION)    
    usernames = list(mentions.values())
    if len(usernames) == 0:
        await update.effective_message.reply_text(queue_user_not_found_message)
        return
    username = usernames[0]
    user_id = context.chat_data.get(username, None)
    if user_id is None:
        await update.effective_message.reply_text(queue_user_not_found_message)
        return
    
    mention = get_mention(user_id, username)
    success = remove_job_if_exists(str(user_id), context)
    if success:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=kick_message.format(name=mention))        
        await clean_up_welcome_message(context, update.effective_chat.id, user_id)
        await clean_up_warn_message(context, update.effective_chat.id, user_id)            
        await context.bot.ban_chat_member(chat_id=context.job.chat_id, user_id=user_id)    


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:    
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def update_announcement_timer(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running scheduled announcement update...")
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
            logger.info("Announcement message found. Updating...")
            msg_object = await context.bot.edit_message_text(chat_id=chat_id, message_id=announcement_id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)        
        except BadRequest as e:
            if e.message == "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                logger.info("Nothing changed. Quitting...")
                return            
                
    if msg_object is None or announcement_id is None:
        logger.info("Announcement message not found. Creating new one...")
        msg_object = await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    
    if msg_object is not None:
        await msg_object.pin(disable_notification=True)
        context.chat_data["announcement_id"] = msg_object.message_id

def get_rave_message(context: ContextTypes.DEFAULT_TYPE):
    cache = context.chat_data.get('cache', Cache(datetime.datetime.now(), []))    
    if not cache.events or len(cache.events) == 0 or (datetime.datetime.now().date() - cache.last_update.date()).days >= 1:
        update_cache(context)

    message = upcoming_events_header
    if len(cache.events) == 0:
        message += no_upcoming_events_message
    else:
        for event in cache.events:
            message += str(event) + '\n'

    return message

def update_cache(context: ContextTypes.DEFAULT_TYPE):
    events = get_events()
    cache = context.chat_data.get('cache', Cache(datetime.datetime.now(), []))    
    cache.update(events)
    context.chat_data['cache'] = cache
    logger.info("Cache updated")

async def warn_idle(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    username = context.chat_data.get(str(user_id), None)
    mention = get_mention(user_id, username)

    message = warn_message.format(name=mention)
    warn_msg = await context.bot.send_message(chat_id=context.job.chat_id, text=message, parse_mode=ParseMode.HTML)    

    context.chat_data['warn_' + str(user_id)] = warn_msg.message_id

    context.job_queue.run_once(kick_idle, when=30*60, chat_id=context.job.chat_id, user_id=user_id, name=str(user_id))

async def kick_idle(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    username = context.chat_data.pop(str(user_id), None)
    mention = get_mention(user_id, username)

    message = kick_message.format(name=mention)

    await context.bot.send_message(chat_id=context.job.chat_id, text=message, parse_mode=ParseMode.HTML)
    await context.bot.ban_chat_member(chat_id=context.job.chat_id, user_id=context.job.user_id)
    await context.bot.unban_chat_member(chat_id=context.job.chat_id, user_id=context.job.user_id, only_if_banned=True)

    await clean_up_welcome_message(context, context.job.chat_id, user_id)
    await clean_up_warn_message(context, context.job.chat_id, user_id)

async def clean_up_welcome_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    welcome_msg_id = context.chat_data.pop('welcome_' + str(user_id), None)
    if welcome_msg_id is not None:
        await context.bot.delete_message(chat_id=chat_id, message_id=welcome_msg_id)
    else:
        logger.warning(f"Welcome message for user {user_id} not found.")

async def clean_up_warn_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    warn_msg_id = context.chat_data.pop('warn_' + str(user_id), None)
    if warn_msg_id is not None:
        await context.bot.delete_message(chat_id=chat_id, message_id=warn_msg_id)
    else:
        logger.warning(f"Warn message for user {user_id} not found.")

if __name__ == '__main__':
    persistence = PicklePersistence('bot_data')
    application = ApplicationBuilder().token(BotConfiguration.token).persistence(persistence).build()
    
    rave_handler = CommandHandler('rave', rave_command)
    application.add_handler(rave_handler)

    update_hander = CommandHandler('update', update_command)
    application.add_handler(update_hander)

    help_handler = CommandHandler('help', help_command)
    application.add_handler(help_handler)

    set_handler = CommandHandler('set', set_command)
    application.add_handler(set_handler)

    unset_handler = CommandHandler('unset', unset_command)
    application.add_handler(unset_handler)

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_welcome_command))
    
    whois_handler = MessageHandler(filters.Regex(r'(?i)(^|\s+)#whois($|\s+)'), whois_reply_command)
    application.add_handler(whois_handler)

    create_event_handler = CommandHandler('createevent', create_event_command)
    application.add_handler(create_event_handler)

    guest_list_handler = CommandHandler('guestlist', guest_list_command)
    application.add_handler(guest_list_handler)

    kick_handler = CommandHandler('kick', kick_command)
    application.add_handler(kick_handler)

    application.run_polling()

