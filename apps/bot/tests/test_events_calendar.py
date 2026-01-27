import pytest
from unittest.mock import patch, MagicMock
import datetime
from events_calendar import (
    get_events,
    search_event,
    create_calendar_event,
    get_calendar_link,
)
from models import Event


class TestGetEvents:
    @patch("events_calendar.requests.get")
    def test_get_events_success(self, mock_get):
        """Test successful events retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "events": [
                {
                    "id": "1",
                    "title": "Test Event 1",
                    "start_dt": "2024-01-15T20:00:00+00:00",
                    "end_dt": "2024-01-15T23:00:00+00:00",
                    "location": "Venue 1",
                    "custom": {"url": "https://example.com/1"},
                    "notes": "Description 1",
                },
                {
                    "id": "2",
                    "title": "Test Event 2",
                    "start_dt": "2024-01-16T20:00:00+00:00",
                    "end_dt": "2024-01-16T23:00:00+00:00",
                    "location": "Venue 2",
                    "custom": {"url": "https://example.com/2"},
                    "notes": "Description 2",
                },
            ]
        }
        mock_get.return_value = mock_response

        events = get_events()

        assert len(events) == 2
        assert events[0].title == "Test Event 1"
        assert events[0].event_id == "1"
        assert events[1].title == "Test Event 2"

    @patch("events_calendar.requests.get")
    def test_get_events_empty(self, mock_get):
        """Test events retrieval with no events"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"events": []}
        mock_get.return_value = mock_response

        events = get_events()

        assert len(events) == 0


class TestSearchEvent:
    @patch("events_calendar.requests.get")
    def test_search_event_found(self, mock_get):
        """Test searching for an event that exists"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "events": [
                {
                    "id": "123",
                    "title": "Test Event",
                    "start_dt": "2024-01-15T20:00:00+00:00",
                    "end_dt": "2024-01-15T23:00:00+00:00",
                    "location": "Test Venue",
                    "custom": {"url": "https://example.com/event"},
                    "notes": "Test description",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = search_event(event)

        assert result is not None
        assert "123" in result

    @patch("events_calendar.requests.get")
    def test_search_event_not_found(self, mock_get):
        """Test searching for an event that doesn't exist"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"events": []}
        mock_get.return_value = mock_response

        result = search_event(event)

        assert result is None

    @patch("events_calendar.requests.get")
    def test_search_event_http_error(self, mock_get):
        """Test searching for an event with HTTP error"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = search_event(event)

        assert result is None


class TestCreateCalendarEvent:
    @patch("events_calendar.requests.post")
    def test_create_calendar_event_success(self, mock_post):
        """Test successful event creation"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = create_calendar_event(event)

        assert result is True
        assert mock_post.called

    @patch("events_calendar.requests.post")
    def test_create_calendar_event_failure(self, mock_post):
        """Test failed event creation"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response

        result = create_calendar_event(event)

        assert result is False


class TestGetCalendarLink:
    def test_get_calendar_link(self):
        """Test getting calendar link"""
        result = get_calendar_link()

        assert result is not None
        assert isinstance(result, str)
