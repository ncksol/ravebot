import datetime
import pytest
from models import Event, Cache


class TestEvent:
    def test_event_initialization(self):
        """Test Event model initialization"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
            event_id="123",
        )

        assert event.title == "Test Event"
        assert event.start_time == "2024-01-15T20:00:00"
        assert event.end_time == "2024-01-15T23:00:00"
        assert event.location == "Test Venue"
        assert event.url == "https://example.com/event"
        assert event.description == "Test description"
        assert event.event_id == "123"

    def test_event_without_event_id(self):
        """Test Event model initialization without event_id"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        assert event.event_id is None

    def test_event_str_representation(self):
        """Test Event string representation"""
        event = Event(
            title="Test Event",
            start_time="2024-01-15T20:00:00",
            end_time="2024-01-15T23:00:00",
            location="Test Venue",
            url="https://example.com/event",
            description="Test description",
        )

        result = str(event)
        assert "15.01" in result
        assert "Test Event" in result
        assert "Test Venue" in result
        assert "https://example.com/event" in result


class TestCache:
    def test_cache_initialization(self):
        """Test Cache model initialization"""
        now = datetime.datetime.now()
        events = []
        cache = Cache(now, events)

        assert cache.last_update == now
        assert cache.events == events

    def test_cache_update(self):
        """Test Cache update method"""
        old_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        cache = Cache(old_time, [])

        new_events = [
            Event(
                title="Event 1",
                start_time="2024-01-15T20:00:00",
                end_time="2024-01-15T23:00:00",
                location="Venue 1",
                url="https://example.com/1",
                description="Description 1",
            )
        ]

        cache.update(new_events)

        assert cache.events == new_events
        assert cache.last_update > old_time
