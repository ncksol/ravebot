import pytest
from utils import cut_string, get_name, get_mention, format_event_date


class TestCutString:
    def test_cut_string_short(self):
        """Test cut_string with a string shorter than the limit"""
        result = cut_string("Hello", 10)
        assert result == "Hello"
    
    def test_cut_string_exact_length(self):
        """Test cut_string with a string exactly at the limit"""
        result = cut_string("Hello", 5)
        assert result == "Hello"
    
    def test_cut_string_too_long(self):
        """Test cut_string with a string longer than the limit"""
        result = cut_string("Hello World", 8)
        assert result == "Hello..."
        assert len(result) == 8
    
    def test_cut_string_empty(self):
        """Test cut_string with empty string"""
        result = cut_string("", 10)
        assert result == ""


class TestGetName:
    def test_get_name_with_last_name(self):
        """Test get_name with both first and last name"""
        result = get_name("John", "Doe")
        assert result == "John Doe"
    
    def test_get_name_without_last_name(self):
        """Test get_name with only first name"""
        result = get_name("John", None)
        assert result == "John"
    
    def test_get_name_empty_first_name(self):
        """Test get_name with empty first name"""
        result = get_name("", "Doe")
        assert result == " Doe"


class TestGetMention:
    def test_get_mention(self):
        """Test get_mention HTML generation"""
        result = get_mention(123456, "John Doe")
        assert result == "<a href='tg://user?id=123456'>John Doe</a>"
    
    def test_get_mention_with_special_chars(self):
        """Test get_mention with special characters in name"""
        result = get_mention(123456, "John & Doe")
        assert result == "<a href='tg://user?id=123456'>John & Doe</a>"


class TestFormatEventDate:
    def test_format_event_date_with_timezone(self):
        """Test format_event_date with timezone format"""
        result = format_event_date("2024-01-15T20:00:00+0000", "%Y-%m-%dT%H:%M:%S%z")
        assert result == "2024-01-15T20:00:00"
    
    def test_format_event_date_without_timezone(self):
        """Test format_event_date without timezone"""
        result = format_event_date("2024-01-15T20:00:00", "%Y-%m-%dT%H:%M:%S")
        assert result == "2024-01-15T20:00:00"
