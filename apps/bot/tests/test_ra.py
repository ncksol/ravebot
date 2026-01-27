import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
from ra import get_ra_event, process_ra_event


class TestGetRaEvent:
    @patch(
        "ra.open",
        new_callable=mock_open,
        read_data='{"query": "test", "variables": {}}',
    )
    @patch("ra.requests.post")
    def test_get_ra_event_success(self, mock_post, mock_file):
        """Test successful RA event retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "title": "Test Event",
                    "content": "Test description",
                    "startTime": "2024-01-15T20:00:00.000",
                    "endTime": "2024-01-15T23:00:00.000",
                    "venue": {"name": "Test Venue"},
                }
            }
        }
        mock_post.return_value = mock_response

        result = get_ra_event("12345")

        assert result["title"] == "Test Event"
        assert result["content"] == "Test description"
        assert mock_post.called

    @patch(
        "ra.open",
        new_callable=mock_open,
        read_data='{"query": "test", "variables": {}}',
    )
    @patch("ra.requests.post")
    def test_get_ra_event_http_error(self, mock_post, mock_file):
        """Test RA event retrieval with HTTP error"""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Not found")
        )
        mock_post.return_value = mock_response

        result = get_ra_event("12345")

        assert result is None

    @patch(
        "ra.open",
        new_callable=mock_open,
        read_data='{"query": "test", "variables": {}}',
    )
    @patch("ra.requests.post")
    def test_get_ra_event_no_data(self, mock_post, mock_file):
        """Test RA event retrieval with no data in response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errors": ["Some error"]}
        mock_post.return_value = mock_response

        result = get_ra_event("12345")

        assert result is None


class TestProcessRaEvent:
    @pytest.mark.asyncio
    async def test_process_ra_event_valid_url(self):
        """Test processing RA event with valid URL"""
        url = "https://ra.co/events/12345"

        with patch("ra.get_ra_event") as mock_get:
            mock_get.return_value = {
                "title": "Test Event",
                "content": "Test description",
                "startTime": "2024-01-15T20:00:00.000",
                "endTime": "2024-01-15T23:00:00.000",
                "venue": {"name": "Test Venue"},
            }

            event = await process_ra_event(url)

            assert event is not None
            assert event.title == "Test Event"
            assert event.description == "Test description"
            assert event.location == "Test Venue"
            assert event.url == url
            assert event.start_time == "2024-01-15T20:00:00"
            assert event.end_time == "2024-01-15T23:00:00"

    @pytest.mark.asyncio
    async def test_process_ra_event_invalid_url(self):
        """Test processing RA event with invalid URL"""
        url = "https://example.com/events/12345"

        event = await process_ra_event(url)

        assert event is None

    @pytest.mark.asyncio
    async def test_process_ra_event_no_data(self):
        """Test processing RA event when API returns no data"""
        url = "https://ra.co/events/12345"

        with patch("ra.get_ra_event") as mock_get:
            mock_get.return_value = None

            event = await process_ra_event(url)

            assert event is None
