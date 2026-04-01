import requests
from requests.adapters import HTTPAdapter
from typing import Optional

def build_http_session(retries: int = 3) -> requests.Session:
    """
    Create a requests Session with retry logic and browser-like headers.
    """
    sess = requests.Session()
    adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=retries)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    return sess

def truncate_words(text: str, limit: int) -> str:
    """
    Truncate text to a maximum number of words.
    """
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + "..."
