import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import datetime
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from main import (
    remove_job_if_exists,
    get_rave_message,
    update_cache,
    is_old_command
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


class TestUpdateCache:
    @patch('main.get_events')
    def test_update_cache_new_events(self, mock_get_events):
        """Test updating cache with new events"""
        mock_events = [
            Event(
                title="Event 1",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Venue 1",
                url="https://example.com/1",
                description="Description 1"
            )
        ]
        mock_get_events.return_value = mock_events
        
        context = MagicMock()
        context.chat_data = {}
        
        update_cache(context)
        
        assert 'cache' in context.chat_data
        assert context.chat_data['cache'].events == mock_events
        mock_get_events.assert_called_once()


class TestGetRaveMessage:
    @patch('main.update_cache')
    @patch('main.get_events')
    def test_get_rave_message_with_events(self, mock_get_events, mock_update_cache):
        """Test getting rave message with events"""
        events = [
            Event(
                title="Event 1",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Venue 1",
                url="https://example.com/1",
                description="Description 1"
            )
        ]
        
        context = MagicMock()
        cache = Cache(datetime.datetime.now(), events)
        context.chat_data = {'cache': cache}
        
        message = get_rave_message(context)
        
        assert "Event 1" in message
        assert "Venue 1" in message
    
    @patch('main.update_cache')
    def test_get_rave_message_no_events(self, mock_update_cache):
        """Test getting rave message with no events"""
        context = MagicMock()
        cache = Cache(datetime.datetime.now(), [])
        context.chat_data = {'cache': cache}
        
        message = get_rave_message(context)
        
        assert message is not None
    
    @patch('main.update_cache')
    def test_get_rave_message_outdated_cache(self, mock_update_cache):
        """Test getting rave message with outdated cache"""
        old_date = datetime.datetime.now() - datetime.timedelta(days=2)
        context = MagicMock()
        cache = Cache(old_date, [])
        context.chat_data = {'cache': cache}
        
        message = get_rave_message(context)
        
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
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=120)
        update.message.date = old_time
        context = MagicMock()
        
        result = is_old_command(update, context)
        
        assert result is True


class TestCommandHandlers:
    @pytest.mark.asyncio
    async def test_rave_command_basic(self):
        """Test basic rave command execution"""
        from main import rave_command
        
        update = MagicMock()
        update.message.date = datetime.datetime.now(datetime.timezone.utc)
        update.effective_chat.id = 12345
        
        context = MagicMock()
        context.bot.send_message = AsyncMock()
        cache = Cache(datetime.datetime.now(), [])
        context.chat_data = {'cache': cache}
        
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
