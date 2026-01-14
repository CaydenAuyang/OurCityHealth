import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime, timezone

from backend.app.models import Entry
from backend.app.scrape.utils import build_http_session

DEFAULT_HEADERS = {
    "User-Agent": "OurCityHealth/1.0",
}

def safe_request(url: str, headers: Dict[str, str], timeout: int, max_retries: int) -> Optional[str]:
    session = build_http_session(retries=max_retries)
    try:
        resp = session.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None

def reddit_fetch_subreddit_json(sub: str, max_pages: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    after: Optional[str] = None
    
    for _ in range(max_pages):
        bases = (
            f"https://api.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
            f"https://old.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
            f"https://www.reddit.com/r/{sub}/.json?limit=50&raw_json=1",
        )
        jtxt = None
        for base in bases:
            url = base + (f"&after={after}" if after else "")
            jtxt = safe_request(url, headers={**DEFAULT_HEADERS, "Accept": "application/json", "Referer": f"https://www.reddit.com/r/{sub}/"}, timeout=12, max_retries=4)
            if jtxt:
                break
        if not jtxt:
            break
            
        try:
            data = json.loads(jtxt)
        except Exception:
            break
            
        children = data.get('data', {}).get('children', [])
        if not children:
            break
            
        for ch in children:
            d = ch.get('data', {})
            permalink = d.get('permalink')
            title = d.get('title', '')
            
            full_url = urljoin("https://www.reddit.com/", permalink) if permalink else None
            
            created = d.get('created_utc')
            iso_date = None
            if isinstance(created, (int, float)):
                iso_date = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
            
            if full_url:
                items.append({
                    "url": full_url,
                    "title": title,
                    "date": iso_date,
                    "permalink": permalink
                })
        
        after = data.get('data', {}).get('after')
        if not after:
            break
        time.sleep(0.5)
    
    return items

def reddit_fetch_comments_json(permalink: str, limit: int) -> List[str]:
    bases = (
        "https://api.reddit.com",
        "https://old.reddit.com",
        "https://www.reddit.com",
    )
    jtxt = None
    for host in bases:
        url = urljoin(host, permalink) + ".json?limit=50&raw_json=1"
        jtxt = safe_request(url, headers={**DEFAULT_HEADERS, "Accept": "application/json", "Referer": url}, timeout=12, max_retries=4)
        if jtxt:
            break
    if not jtxt:
        return []
    
    try:
        data = json.loads(jtxt)
    except Exception:
        return []
    
    out: List[str] = []
    
    if isinstance(data, list) and len(data) > 1:
        comments_listing = data[1]
        for ch in comments_listing.get('data', {}).get('children', []):
            if ch.get('kind') != 't1':
                continue
            
            body = ch.get('data', {}).get('body')
            if body:
                out.append(body.strip())
            
            if len(out) >= limit:
                break
    
    return out

def scrape_reddit_for_cities(city_subreddits: Dict[str, str], max_pages: int, comments_per_post_limit: int) -> List[Entry]:
    all_entries: List[Entry] = []
    
    for city, sub in city_subreddits.items():
        print(f"[reddit] Scraping r/{sub} for {city}")
        posts = reddit_fetch_subreddit_json(sub, max_pages)
        
        for p in posts:
            all_entries.append(Entry(
                source="RedditPost",
                source_site=f"r/{sub}",
                url=p["url"],
                title=p["title"],
                date=p["date"],
                text=p["title"],
                cities=[city],
                permalink=p["permalink"]
            ))

        permalinks = [(p, p.get("permalink")) for p in posts if p.get("permalink")]
        comments_by_post: Dict[str, List[str]] = {}
        
        if permalinks:
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(reddit_fetch_comments_json, pl, comments_per_post_limit): p for p, pl in permalinks}
                for fut in as_completed(futs):
                    post = futs[fut]
                    try:
                        comments_by_post[post["url"]] = fut.result() or []
                    except Exception:
                        comments_by_post[post["url"]] = []
                        
        for p in posts:
            for c in comments_by_post.get(p["url"], []):
                all_entries.append(Entry(
                    source="RedditComment",
                    source_site=f"r/{sub}",
                    url=p["url"],
                    title=p["title"],
                    date=p["date"],
                    text=c,
                    cities=[city]
                ))
            time.sleep(0.01)
            
    return all_entries
