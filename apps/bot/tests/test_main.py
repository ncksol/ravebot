import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import datetime
from telegram import Update, User, Chat, Message
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes
from main import (
    get_configured_announcement_job_name,
    register_configured_announcement_job,
    remove_job_if_exists,
    get_rave_message,
    update_cache,
    is_old_command,
    update_announcement_timer,
)
from models import Cache, Event


class TestRemoveJobIfExists:
    def test_remove_job_if_exists_job_found(self):
        """Test removing an existing job"""
        context = MagicMock()
        mock_job = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = [mock_job]

        result = remove_job_if_exists("test_job", context)

        assert result is True
        mock_job.schedule_removal.assert_called_once()

    def test_remove_job_if_exists_no_job(self):
        """Test removing a non-existent job"""
        context = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = []

        result = remove_job_if_exists("test_job", context)

        assert result is False

    def test_remove_job_if_exists_multiple_jobs(self):
        """Test removing multiple jobs with same name"""
        context = MagicMock()
        mock_job1 = MagicMock()
        mock_job2 = MagicMock()
        context.job_queue.get_jobs_by_name.return_value = [mock_job1, mock_job2]

        result = remove_job_if_exists("test_job", context)

        assert result is True
        mock_job1.schedule_removal.assert_called_once()
        mock_job2.schedule_removal.assert_called_once()


class TestConfiguredAnnouncementJob:
    def test_get_configured_announcement_job_name(self):
        assert (
            get_configured_announcement_job_name(-1001234567890)
            == "configured_update_-1001234567890"
        )

    def test_register_configured_announcement_job_skips_when_chat_not_configured(
        self, monkeypatch
    ):
        import main

        monkeypatch.setattr(main.AnnouncementConfiguration, "chat_id", None)
        application = MagicMock()

        result = register_configured_announcement_job(application)

        assert result is False
        application.job_queue.get_jobs_by_name.assert_not_called()
        application.job_queue.run_repeating.assert_not_called()

    def test_register_configured_announcement_job_is_idempotent(self):
        application = MagicMock()
        existing_job = MagicMock()
        application.job_queue.get_jobs_by_name.return_value = [existing_job]
        chat_id = -1001234567890

        result = register_configured_announcement_job(
            application,
            chat_id=chat_id,
            interval_seconds=1800,
            first_run_seconds=15,
        )

        assert result is True
        existing_job.schedule_removal.assert_called_once()
        application.job_queue.get_jobs_by_name.assert_called_once_with(
            get_configured_announcement_job_name(chat_id)
        )
        application.job_queue.run_repeating.assert_called_once_with(
            update_announcement_timer,
            interval=1800,
            first=15,
            chat_id=chat_id,
            name=get_configured_announcement_job_name(chat_id),
        )


class TestUpdateAnnouncement:
    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_edits_existing_message(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Upcoming events</b>"
        edited_message = MagicMock()
        edited_message.message_id = 111
        edited_message.pin = AsyncMock()

        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(return_value=edited_message)
        context.bot.send_message = AsyncMock()

        await update_announcement(context, -1001234567890)

        context.bot.edit_message_text.assert_called_once()
        context.bot.send_message.assert_not_called()
        edited_message.pin.assert_called_once_with(disable_notification=True)
        assert context.chat_data["announcement_id"] == 111
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "success"

    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_treats_not_modified_as_success(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Upcoming events</b>"
        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(
            side_effect=BadRequest("Message is not modified")
        )
        context.bot.send_message = AsyncMock()

        await update_announcement(context, -1001234567890)

        context.bot.send_message.assert_not_called()
        assert context.chat_data["announcement_id"] == 111
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "success"
        assert (
            "not modified" in context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["reason"]
        )

    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_recovers_from_stale_message_id(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Upcoming events</b>"
        new_message = MagicMock()
        new_message.message_id = 222
        new_message.pin = AsyncMock()

        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(
            side_effect=BadRequest("Message to edit not found")
        )
        context.bot.send_message = AsyncMock(return_value=new_message)
        context.bot.unpin_chat_message = AsyncMock()
        context.bot.delete_message = AsyncMock()

        await update_announcement(context, -1001234567890)

        context.bot.send_message.assert_called_once()
        new_message.pin.assert_called_once_with(disable_notification=True)
        assert context.chat_data["announcement_id"] == 222
        context.bot.unpin_chat_message.assert_called_once_with(
            chat_id=-1001234567890, message_id=111
        )
        context.bot.delete_message.assert_called_once_with(
            chat_id=-1001234567890, message_id=111
        )
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "success"

    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_does_not_create_new_message_for_bad_html(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Broken"
        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(
            side_effect=BadRequest("Can't parse entities")
        )
        context.bot.send_message = AsyncMock()

        await update_announcement(context, -1001234567890)

        context.bot.send_message.assert_not_called()
        assert context.chat_data["announcement_id"] == 111
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "failure"

    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_records_failure_when_send_message_raises(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Upcoming events</b>"
        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(
            side_effect=BadRequest("Message to edit not found")
        )
        context.bot.send_message = AsyncMock(side_effect=TelegramError("Network error"))

        await update_announcement(context, -1001234567890)

        context.bot.send_message.assert_called_once()
        assert context.chat_data["announcement_id"] == 111
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "failure"
        assert (
            "create failed" in context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["reason"]
        )

    @pytest.mark.asyncio
    @patch("main.get_rave_message", new_callable=AsyncMock)
    async def test_update_announcement_records_failure_and_keeps_new_id_when_pin_raises(
        self, mock_get_rave_message
    ):
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, update_announcement

        mock_get_rave_message.return_value = "<b>Upcoming events</b>"
        new_message = MagicMock()
        new_message.message_id = 222
        new_message.pin = AsyncMock(side_effect=TelegramError("Can't pin"))

        context = MagicMock()
        context.chat_data = {"announcement_id": 111}
        context.bot_data = {}
        context.bot.edit_message_text = AsyncMock(
            side_effect=BadRequest("Message to edit not found")
        )
        context.bot.send_message = AsyncMock(return_value=new_message)
        context.bot.unpin_chat_message = AsyncMock()
        context.bot.delete_message = AsyncMock()

        await update_announcement(context, -1001234567890)

        assert context.chat_data["announcement_id"] == 222
        assert context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["outcome"] == "failure"
        assert "pin failed" in context.bot_data[LAST_ANNOUNCEMENT_UPDATE_KEY]["reason"]
        context.bot.unpin_chat_message.assert_not_called()
        context.bot.delete_message.assert_not_called()


class TestUpdateCache:
    @pytest.mark.asyncio
    @patch("main.get_events")
    async def test_update_cache_new_events(self, mock_get_events):
        """Test updating cache with new events"""
        mock_events = [
            Event(
                title="Event 1",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Venue 1",
                url="https://example.com/1",
                description="Description 1",
            )
        ]
        mock_get_events.return_value = mock_events

        context = MagicMock()
        context.chat_data = {}

        await update_cache(context)

        assert "cache" in context.chat_data
        assert context.chat_data["cache"].events == mock_events
        mock_get_events.assert_called_once()

    @pytest.mark.asyncio
    @patch("main.get_events")
    async def test_update_cache_keeps_existing_cache_on_api_failure(self, mock_get_events):
        existing_events = [
            Event(
                title="Existing Event",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Existing Venue",
                url="https://example.com/existing",
                description="Existing description",
            )
        ]
        existing_cache = Cache(datetime.datetime(2024, 1, 1), existing_events)
        mock_get_events.return_value = None
        context = MagicMock()
        context.chat_data = {"cache": existing_cache}

        await update_cache(context)

        assert context.chat_data["cache"] is existing_cache
        assert context.chat_data["cache"].events == existing_events

    @pytest.mark.asyncio
    @patch("main.get_events")
    async def test_update_cache_accepts_empty_calendar_response(self, mock_get_events):
        existing_events = [
            Event(
                title="Existing Event",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Existing Venue",
                url="https://example.com/existing",
                description="Existing description",
            )
        ]
        existing_cache = Cache(datetime.datetime(2024, 1, 1), existing_events)
        mock_get_events.return_value = []
        context = MagicMock()
        context.chat_data = {"cache": existing_cache}

        await update_cache(context)

        assert context.chat_data["cache"] is existing_cache
        assert context.chat_data["cache"].events == []
        assert context.chat_data["cache"].last_update.date() == datetime.datetime.now().date()


class TestGetRaveMessage:
    @pytest.mark.asyncio
    @patch("main.update_cache", new_callable=AsyncMock)
    @patch("main.get_events")
    async def test_get_rave_message_with_events(
        self, mock_get_events, mock_update_cache
    ):
        """Test getting rave message with events"""
        events = [
            Event(
                title="Event 1",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Venue 1",
                url="https://example.com/1",
                description="Description 1",
            )
        ]

        context = MagicMock()
        cache = Cache(datetime.datetime.now(), events)
        context.chat_data = {"cache": cache}

        message = await get_rave_message(context)

        assert "Event 1" in message
        assert "Venue 1" in message

    @pytest.mark.asyncio
    @patch("main.update_cache", new_callable=AsyncMock)
    async def test_get_rave_message_no_events(self, mock_update_cache):
        """Test getting rave message with no events"""
        context = MagicMock()
        cache = Cache(datetime.datetime.now(), [])
        context.chat_data = {"cache": cache}

        message = await get_rave_message(context)

        assert message is not None

    @pytest.mark.asyncio
    @patch("main.update_cache", new_callable=AsyncMock)
    async def test_get_rave_message_outdated_cache(self, mock_update_cache):
        """Test getting rave message with outdated cache"""
        old_date = datetime.datetime.now() - datetime.timedelta(days=2)
        context = MagicMock()
        cache = Cache(old_date, [])
        context.chat_data = {"cache": cache}

        message = await get_rave_message(context)

        mock_update_cache.assert_called_once_with(context)


class TestIsOldCommand:
    def test_is_old_command_fresh(self):
        """Test is_old_command with fresh command"""
        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        context = MagicMock()

        result = is_old_command(update, context)

        assert result is False

    def test_is_old_command_old(self):
        """Test is_old_command with old command"""
        update = MagicMock()
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=120
        )
        update.message.date = old_time
        context = MagicMock()

        result = is_old_command(update, context)

        assert result is True


class TestCommandHandlers:
    @pytest.mark.asyncio
    @patch("main.get_events")
    async def test_rave_command_basic(self, mock_get_events):
        """Test basic rave command execution"""
        from main import rave_command

        mock_get_events.return_value = []

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_chat.id = 12345

        context = MagicMock()
        context.bot.send_message = AsyncMock()
        cache = Cache(datetime.datetime.now(), [])
        context.chat_data = {"cache": cache}

        await rave_command(update, context)

        context.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command execution"""
        from main import help_command

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_chat.id = 12345

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        await help_command(update, context)

        context.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_calendar_command(self):
        """Test calendar command execution"""
        from main import calendar_command

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_chat.id = 12345

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        await calendar_command(update, context)

        context.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_command_configured_chat(self):
        """Test set_command when chat_id equals configured announcement chat"""
        from main import set_command

        configured_chat_id = -1001234567890

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_user.id = 12345
        update.effective_message.chat_id = configured_chat_id
        update.effective_message.reply_text = AsyncMock()

        manual_job = MagicMock()
        context = MagicMock()
        context.application = MagicMock()
        context.bot_data = {"update_timers": {configured_chat_id: True}}
        context.job_queue.get_jobs_by_name.return_value = [manual_job]

        with patch("main.BotConfiguration.admin_id", 12345):
            with patch("main.AnnouncementConfiguration.chat_id", configured_chat_id):
                await set_command(update, context)

        manual_job.schedule_removal.assert_called_once()
        from text import configured_announcement_set_message

        update.effective_message.reply_text.assert_called_once_with(
            configured_announcement_set_message
        )
        context.application.job_queue.run_repeating.assert_called_once()
        assert configured_chat_id not in context.bot_data["update_timers"]

    @pytest.mark.asyncio
    async def test_unset_command_configured_chat(self):
        """Test unset_command when chat_id equals configured announcement chat"""
        from main import unset_command
        from text import configured_announcement_unset_message

        configured_chat_id = -1001234567890

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_user.id = 12345
        update.effective_message.chat_id = configured_chat_id
        update.effective_message.reply_text = AsyncMock()

        context = MagicMock()
        context.bot_data = {"update_timers": {configured_chat_id: True}}

        with patch("main.BotConfiguration.admin_id", 12345):
            with patch("main.AnnouncementConfiguration.chat_id", configured_chat_id):
                await unset_command(update, context)

        update.effective_message.reply_text.assert_called_once_with(
            configured_announcement_unset_message
        )
        context.job_queue.get_jobs_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_status_command_reports_announcement_configuration(self, monkeypatch):
        import main
        from main import LAST_ANNOUNCEMENT_UPDATE_KEY, status_command

        monkeypatch.setattr(main.BotConfiguration, "admin_id", 123456)
        monkeypatch.setattr(main.AnnouncementConfiguration, "chat_id", -1001234567890)

        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_user.id = 123456
        update.effective_message.reply_html = AsyncMock()

        context = MagicMock()
        context.chat_data = {
            "announcement_id": 222,
            "cache": Cache(datetime.datetime.now(), []),
        }
        context.bot_data = {
            LAST_ANNOUNCEMENT_UPDATE_KEY: {
                "timestamp": "2026-06-05 10:00:00",
                "outcome": "success",
                "reason": "announcement updated",
            }
        }
        context.job_queue.jobs.return_value = [MagicMock()]
        context.job_queue.get_jobs_by_name.return_value = [MagicMock()]

        await status_command(update, context)

        status_text = update.effective_message.reply_html.call_args.args[0]
        assert "📌 Announcement config: Enabled" in status_text
        assert "📌 Announcement job: Active" in status_text
        assert "📌 Announcement message: 222" in status_text
        assert "🧾 Last announcement update: success at 2026-06-05 10:00:00" in status_text
