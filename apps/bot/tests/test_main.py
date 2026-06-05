import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import datetime
from telegram import Update, User, Chat, Message
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
        update.effective_message.reply_text.assert_called_once_with(
            "Configured announcement updater is managed by deployment and is active."
        )
        assert configured_chat_id not in context.bot_data["update_timers"]
