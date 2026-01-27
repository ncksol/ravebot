import pytest
from unittest.mock import patch, MagicMock
import json
from dice import get_dice_event_id, process_dice_event, get_event_details


class TestGetDiceEventId:
    @patch('dice.urllib.request.urlopen')
    def test_get_dice_event_id_success(self, mock_urlopen):
        """Test successful dice event ID extraction"""
        html_content = b'''
        <html>
            <head>
                <meta property="product:retailer_item_id" content="12345" />
            </head>
        </html>
        '''
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = html_content
        mock_urlopen.return_value = mock_response
        
        result = get_dice_event_id("https://dice.fm/event/test")
        
        assert result == "12345"
    
    @patch('dice.urllib.request.urlopen')
    def test_get_dice_event_id_no_meta_tag(self, mock_urlopen):
        """Test dice event ID extraction when meta tag is missing"""
        html_content = b'<html><head></head></html>'
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = html_content
        mock_urlopen.return_value = mock_response
        
        result = get_dice_event_id("https://dice.fm/event/test")
        
        assert result is None
    
    @patch('dice.urllib.request.urlopen')
    def test_get_dice_event_id_http_error(self, mock_urlopen):
        """Test dice event ID extraction with HTTP error"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.read.return_value = b''
        mock_urlopen.return_value = mock_response
        
        result = get_dice_event_id("https://dice.fm/event/test")
        
        assert result is None


class TestGetEventDetails:
    @patch('dice.urllib.request.urlopen')
    def test_get_event_details_success(self, mock_urlopen):
        """Test successful event details retrieval"""
        event_data = {
            "about": {"description": "Test description"},
            "name": "Test Event",
            "dates": {
                "event_start_date": "2024-01-15T20:00:00+0000",
                "event_end_date": "2024-01-15T23:00:00+0000"
            },
            "venues": [{"address": "Test Venue Address"}]
        }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(event_data).encode()
        mock_urlopen.return_value = mock_response
        
        result = get_event_details("12345")
        
        assert result["name"] == "Test Event"
        assert result["description"] == "Test description"
        assert result["venue_address"] == "Test Venue Address"
    
    @patch('dice.urllib.request.urlopen')
    def test_get_event_details_http_error(self, mock_urlopen):
        """Test event details retrieval with HTTP error"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value = mock_response
        
        result = get_event_details("12345")
        
        assert result == {}


class TestProcessDiceEvent:
    @pytest.mark.asyncio
    async def test_process_dice_event_success(self):
        """Test successful dice event processing"""
        url = "https://dice.fm/event/test"
        
        with patch('dice.get_dice_event_id') as mock_get_id, \
             patch('dice.get_event_details') as mock_get_details:
            
            mock_get_id.return_value = "12345"
            mock_get_details.return_value = {
                "name": "Test Event",
                "description": "Test description",
                "start_date": "2024-01-15T20:00:00",
                "end_date": "2024-01-15T23:00:00",
                "venue_address": "Test Venue"
            }
            
            event = await process_dice_event(url)
            
            assert event is not None
            assert event.title == "Test Event"
            assert event.description == "Test description"
            assert event.location == "Test Venue"
            assert event.url == url
    
    @pytest.mark.asyncio
    async def test_process_dice_event_no_event_id(self):
        """Test dice event processing when event ID cannot be extracted"""
        url = "https://dice.fm/event/test"
        
        with patch('dice.get_dice_event_id') as mock_get_id:
            mock_get_id.return_value = None
            
            event = await process_dice_event(url)
            
            assert event is None
    
    @pytest.mark.asyncio
    async def test_process_dice_event_no_details(self):
        """Test dice event processing when details cannot be retrieved"""
        url = "https://dice.fm/event/test"
        
        with patch('dice.get_dice_event_id') as mock_get_id, \
             patch('dice.get_event_details') as mock_get_details:
            
            mock_get_id.return_value = "12345"
            mock_get_details.return_value = None
            
            event = await process_dice_event(url)
            
            assert event is None
