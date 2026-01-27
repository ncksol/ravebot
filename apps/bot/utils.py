import logging
import datetime
import sys
import json
from urllib.parse import urlparse, urlunparse

from settings import LoggingConfiguration


# Configure root logger to capture ALL logs (including from python-telegram-bot)
def setup_logging():
    """Configure logging for the entire application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    # Use JSON format if configured, otherwise use standard format
    if LoggingConfiguration.json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    root_logger.addHandler(handler)

    # Reduce noise from HTTP libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Custom JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Initialize logging on module import
setup_logging()

# Get logger for this module (and export for other modules to use)
logger = logging.getLogger(__name__)


def cut_string(string: str, length: int):
    if len(string) > length:
        string = string[: length - 3] + "..."
    return string


def get_name(first_name: str, last_name: str) -> str:
    if last_name is not None:
        return f"{first_name} {last_name}"
    return first_name


def get_mention(user_id: int, name: str) -> str:
    return f"<a href='tg://user?id={str(user_id)}'>{name}</a>"


def format_event_date(date: str, format: str) -> str:
    return datetime.datetime.strptime(date, format).strftime("%Y-%m-%dT%H:%M:%S")


def validate_and_sanitize_url(
    url: str, allowed_domains: list
) -> tuple[bool, str | None, str | None, str | None]:
    """
    Validates and sanitizes a URL for security.

    Args:
        url: The URL to validate
        allowed_domains: List of allowed domains (e.g., ['ra.co', 'dice.fm'])

    Returns:
        tuple: (is_valid: bool, sanitized_url: str or None, error_message: str or None, domain: str or None)
    """
    try:
        # Parse the URL
        parsed = urlparse(url.strip())

        # Check if URL has a scheme
        if not parsed.scheme:
            return (False, None, "URL must include a scheme (https://)", None)

        # Validate that the scheme is https
        if parsed.scheme.lower() != "https":
            return (
                False,
                None,
                "Only HTTPS URLs are allowed for security reasons",
                None,
            )

        # Check if URL has a domain
        if not parsed.netloc:
            return (False, None, "Invalid URL: missing domain", None)

        # Reject URLs with user authentication (e.g., user@domain or user:pass@domain)
        if parsed.username or parsed.password:
            return (
                False,
                None,
                "URLs with authentication credentials are not allowed",
                None,
            )

        # Extract hostname (without port) for domain validation
        # This prevents bypass attempts with ports like ra.co:8080 or subdomains
        hostname = parsed.hostname
        if not hostname:
            return (False, None, "Invalid URL: missing hostname", None)

        hostname = hostname.lower()

        # Validate domain exactly matches (no subdomain bypass)
        if hostname not in allowed_domains:
            return (
                False,
                None,
                f"Unsupported domain. Only {', '.join(allowed_domains)} are supported",
                hostname,
            )

        # Sanitize the URL by reconstructing it with validated components
        sanitized_url = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

        return (True, sanitized_url, None, hostname)

    except (ValueError, AttributeError) as e:
        # ValueError: from urlparse if URL is malformed
        # AttributeError: if parsed components are not as expected
        logger.error(f"URL validation error: {e}")
        return (False, None, "Malformed URL", None)
