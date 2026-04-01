import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Set
from bs4 import BeautifulSoup
import feedparser

from backend.app.models import Entry
from backend.app.scrape.utils import build_http_session

def parse_rss_for_links(feed_xml: str, limit: int) -> List[str]:
    links: List[str] = []
    if feedparser:
        try:
            fp = feedparser.parse(feed_xml)
            for e in fp.entries[:limit]:
                link = getattr(e, 'link', None)
                if link:
                    links.append(link)
            return links
        except Exception:
            pass
            
    # Fallback simple XML
    try:
        root = ET.fromstring(feed_xml)
        for item in root.findall('.//item'):
            link = item.findtext('link')
            if link:
                links.append(link)
                if len(links) >= limit:
                    break
    except Exception:
        return []
    return links

def extract_links_from_homepage(base_url: str, html: str, limit: int) -> List[str]:
    """
    Extract likely article links from a homepage HTML.
    """
    soup = BeautifulSoup(html, 'html.parser')
    candidates = set()
    base_domain = urlparse(base_url).netloc.replace("www.", "")

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        full_url = urljoin(base_url, href)
        
        # Must be same domain
        if base_domain not in full_url:
            continue
            
        # Heuristic filters for "article-like" URLs
        path = urlparse(full_url).path.lower()
        if len(path) < 10:
            continue
        
        # Avoid common non-article paths
        if any(x in path for x in ['/tag/', '/category/', '/author/', '/page/', '/login', '/signup', '/search']):
            continue
            
        # Require some numeric ID or dashes (common in article slugs)
        if '-' in path or any(c.isdigit() for c in path):
            candidates.add(full_url)
            
        if len(candidates) >= limit:
            break
            
    return list(candidates)

def discover_article_links(base_url: str, session, limit: int) -> List[str]:
    """
    Prefer RSS/sitemap discovery; then TOP-UP with homepage extraction.
    """
    candidates: List[str] = []
    seen: Set[str] = set()

    def add_links(links: List[str]):
        for u in links:
            if u and u not in seen:
                seen.add(u)
                candidates.append(u)

    # Try common RSS endpoints
    rss_paths = ["/rss", "/feed", "/rss.xml", "/feeds/all.rss", "/feeds/rss.xml"]
    for p in rss_paths:
        try:
            resp = session.get(urljoin(base_url, p), timeout=8)
            if resp.status_code == 200 and resp.text:
                links = parse_rss_for_links(resp.text, limit)
                add_links(links)
                if len(candidates) >= limit * 2:
                    break
        except Exception:
            continue

    # Try sitemap
    try:
        resp = session.get(urljoin(base_url, "/sitemap.xml"), timeout=8)
        if resp.status_code == 200 and resp.text:
            try:
                root = ET.fromstring(resp.text)
                for loc in root.findall('.//{*}loc'):
                    url = loc.text or ""
                    if url and any(seg in url for seg in ("/news/", "/article", "/stories", "/world/", "/business/")):
                        add_links([url])
                        if len(candidates) >= limit * 2:
                            break
            except Exception:
                pass
    except Exception:
        pass

    # Fallback/top-up via homepage parsing
    if len(candidates) < limit:
        try:
            homepage_html = session.get(base_url, timeout=8).text
            more = extract_links_from_homepage(base_url, homepage_html, limit)
            add_links(more)
        except Exception:
            pass

    return candidates[: max(limit * 2, len(candidates))]

def extract_title_and_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, 'html.parser')
    
    # Clean
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
        
    title = ''
    og = soup.find('meta', attrs={'property': 'og:title'})
    if og and og.get('content'):
        title = og['content'].strip()
    
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
        
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            
    texts: List[str] = []
    
    # Try common content containers
    roots = [
        soup.find('article'),
        soup.find('main'),
        soup.find(attrs={'role': 'main'}),
        soup.find('div', attrs={'itemprop': 'articleBody'}),
        soup.find('section', class_='article'),
        soup.find('div', id='main-content'),
    ]
    container = next((r for r in roots if r), soup)
    
    ps = container.find_all('p')
    for p in ps:
        t = p.get_text(" ", strip=True)
        if t and len(t.split()) >= 3:
            texts.append(t)
        if len(texts) >= 200:
            break
            
    text = "\n".join(texts)
    return title, text

def scrape_news_site(base_url: str, label: str, limit: int) -> List[Entry]:
    print(f"[news] Scraping {label}")
    entries: List[Entry] = []
    session = build_http_session()
    
    candidates = discover_article_links(base_url, session, limit * 2)
    if not candidates:
        return entries
        
    count = 0
    
    def fetch_one(u: str) -> Optional[Entry]:
        try:
            resp = session.get(u, timeout=8)
            if resp.status_code != 200 or not resp.text:
                return None
            title, text = extract_title_and_text(resp.text)
            if not (title or text) or (len(text.split()) < 5 and len(title) < 2):
                return None
            return Entry(
                source="News",
                source_site=label,
                url=u,
                title=title,
                date=None,
                text=text,
                cities=[]
            )
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(fetch_one, u) for u in candidates[: limit * 3]]
        for i, fut in enumerate(as_completed(futures), 1):
            if count >= limit:
                break
            try:
                res = fut.result()
                if res is not None:
                    entries.append(res)
                    count += 1
            except Exception:
                pass
                
    return entries
