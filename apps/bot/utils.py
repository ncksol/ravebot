import logging, datetime, sys
from urllib.parse import urlparse, urlunparse

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

def cut_string(string: str, length: int):
    if len(string) > length:
        string = string[:length-3] + "..."
    return string

def get_name(first_name: str, last_name: str) -> str:
    if last_name is not None:
        return f"{first_name} {last_name}"
    return first_name

def get_mention(user_id: int, name: str) -> str:
    return f"<a href='tg://user?id={str(user_id)}'>{name}</a>"

def format_event_date(date: str, format: str) -> str:
    return datetime.datetime.strptime(date, format).strftime('%Y-%m-%dT%H:%M:%S')

def validate_and_sanitize_url(url: str, allowed_domains: list) -> tuple[bool, str | None, str | None, str | None]:
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
        if parsed.scheme.lower() != 'https':
            return (False, None, "Only HTTPS URLs are allowed for security reasons", None)
        
        # Check if URL has a domain
        if not parsed.netloc:
            return (False, None, "Invalid URL: missing domain", None)
        
        # Reject URLs with user authentication (e.g., user@domain or user:pass@domain)
        if parsed.username or parsed.password:
            return (False, None, "URLs with authentication credentials are not allowed", None)
        
        # Extract hostname (without port) for domain validation
        # This prevents bypass attempts with ports like ra.co:8080 or subdomains
        hostname = parsed.hostname
        if not hostname:
            return (False, None, "Invalid URL: missing hostname", None)
        
        hostname = hostname.lower()
        
        # Validate domain exactly matches (no subdomain bypass)
        if hostname not in allowed_domains:
            return (False, None, f"Unsupported domain. Only {', '.join(allowed_domains)} are supported", hostname)
        
        # Sanitize the URL by reconstructing it with validated components
        sanitized_url = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return (True, sanitized_url, None, hostname)
        
    except (ValueError, AttributeError) as e:
        # ValueError: from urlparse if URL is malformed
        # AttributeError: if parsed components are not as expected
        logger.error(f"URL validation error: {e}")
        return (False, None, "Malformed URL", None)