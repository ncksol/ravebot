from settings import BotConfiguration

# Translation dictionaries
TRANSLATIONS = {
    'ru': {
        'welcome_message': "Привет {name}. Добро пожаловать в нашу группу. Тут мы обсуждаем разную электронную музыку, делимся интересным треками и организовываем совместные походы на ивенты. Мы стараемся создавать атмосферу теплой домашней тусовки, а поэтому хорошо было бы чтобы окружающие хотя бы немного знали друг о друге. Посему расскажи пожалуйста немного о себе - кто ты, откуда, чем занимаешься, что (или кто) привело тебя к нам в группу и самое главное какие стили электронной музыки тебе наиболее близки (три самых любимых диджея?).\n\r<b>Для того чтобы представиться напиши сообщение в чат c тегом #whois. Если этого не сделать в течении пары часов, то злобный бот тебя кикнет.</b>",
        'success_message': "Спасибо {name}! Очень приятно познакомиться. Чтобы узнать побольше о группе и ее участниках кликай сюда, там вся полезная информация - https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3.",
        'help_message': "Вот ссылка на полезную информацию про группу: https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3",
        'warn_message': "{name} все ещё не представились. У тебя есть еще полчаса прежде чем мы распрощаемся.",
        'kick_message': "{name} не представились и покидают чат.",
        'no_event_url_message': "Вы ссылку на ивент забыли.",
        'unsupported_event_url_message': "К сожалению, я пока умею создавать ивенты только с ra.co и dice.fm",
        'event_created_message': "Ивент добавлен в календарь. Оторвёмся!",
        'event_creation_error_message': "Упс! Что-то пошло не так. Нужно курить логи.",
        'admin_access_error_message': "Ишь чего захотел!",
        'queue_user_not_found_message': "Кого? Нет такого человека в очереди...",
        'guest_list_success_message': "{name} провели через гест лист!",
        'kick_message_admin': "{name}, not today. Sorry!",
        'upcoming_events_header': "<u>На этой неделе мы гуляем тут:</u>\n\n",
        'no_upcoming_events_message': "А нигде мы не гуляем! Дома сидим.",
        'duplicate_event_question_message': "Кажется такой ивент у нас уже есть. Оно?",
        'duplicate_event_message': "А такой ивент у нас уже есть.",
        'duplicate_event_create_button_text': "Создать ивент",
        'duplicate_event_skip_button_text': "Не создавать ивент",
    },
    'en': {
        'welcome_message': "Hi {name}. Welcome to our group. Here we discuss various electronic music, share interesting tracks and organize group outings to events. We try to create a warm, homey atmosphere, so it would be great if everyone knew a bit about each other. Please tell us a bit about yourself - who you are, where you're from, what you do, what (or who) brought you to our group and most importantly what styles of electronic music are closest to you (three favorite DJs?).\n\r<b>To introduce yourself, write a message in the chat with the #whois tag. If you don't do this within a couple of hours, the evil bot will kick you.</b>",
        'success_message': "Thanks {name}! Very nice to meet you. To learn more about the group and its members click here, all useful information is there - https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3.",
        'help_message': "Here's a link to useful information about the group: https://npdgm.notion.site/npdgm/Nice-People-Dancing-to-Good-Music-3525966262c64a9e931a9d7b1dcda7e3",
        'warn_message': "{name} still hasn't introduced themselves. You have another half hour before we say goodbye.",
        'kick_message': "{name} didn't introduce themselves and is leaving the chat.",
        'no_event_url_message': "You forgot the event link.",
        'unsupported_event_url_message': "Sorry, I can only create events from ra.co and dice.fm for now",
        'event_created_message': "Event added to calendar. Let's party!",
        'event_creation_error_message': "Oops! Something went wrong. Need to check the logs.",
        'admin_access_error_message': "Nice try!",
        'queue_user_not_found_message': "Who? No such person in the queue...",
        'guest_list_success_message': "{name} passed through the guest list!",
        'kick_message_admin': "{name}, not today. Sorry!",
        'upcoming_events_header': "<u>This week we're partying here:</u>\n\n",
        'no_upcoming_events_message': "We're not partying anywhere! Staying home.",
        'duplicate_event_question_message': "Looks like we already have this event. Is it?",
        'duplicate_event_message': "We already have this event.",
        'duplicate_event_create_button_text': "Create event",
        'duplicate_event_skip_button_text': "Don't create event",
    }
}

# Get the current language from settings
current_language = getattr(BotConfiguration, 'language', 'ru')

# Helper function to get translated text
def get_text(key: str, lang: str = None) -> str:
    """Get translated text for the given key."""
    language = lang or current_language
    # Fallback to Russian if language not found
    if language not in TRANSLATIONS:
        language = 'ru'
    # Fallback to English if key not found in selected language
    if key not in TRANSLATIONS[language] and language != 'en':
        return TRANSLATIONS.get('en', {}).get(key, key)
    return TRANSLATIONS[language].get(key, key)

# Export messages for backward compatibility
welcome_message = get_text('welcome_message')
success_message = get_text('success_message')
help_message = get_text('help_message')
warn_message = get_text('warn_message')
kick_message = get_text('kick_message')
no_event_url_message = get_text('no_event_url_message')
unsupported_event_url_message = get_text('unsupported_event_url_message')
event_created_message = get_text('event_created_message')
event_creation_error_message = get_text('event_creation_error_message')
admin_access_error_message = get_text('admin_access_error_message')
queue_user_not_found_message = get_text('queue_user_not_found_message')
guest_list_success_message = get_text('guest_list_success_message')
upcoming_events_header = get_text('upcoming_events_header')
no_upcoming_events_message = get_text('no_upcoming_events_message')
duplicate_event_question_message = get_text('duplicate_event_question_message')
duplicate_event_message = get_text('duplicate_event_message')
duplicate_event_create_button_text = get_text('duplicate_event_create_button_text')
duplicate_event_skip_button_text = get_text('duplicate_event_skip_button_text')