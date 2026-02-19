"""
Source Credibility Ranking

Hardcoded 3-tier source classification and ranking/deduplication logic for
selecting the highest-quality citations from a pool of articles.
"""

from __future__ import annotations

from typing import List

# ------------------------------------------------------------------ #
# Tier definitions
# ------------------------------------------------------------------ #

TIER_1 = {
    "reuters.com", "apnews.com", "bbc.co.uk", "bbc.com",
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "ft.com", "economist.com", "wsj.com", "bloomberg.com",
    "aljazeera.com", "dw.com", "france24.com", "nhk.or.jp",
    "scmp.com", "straitstimes.com", "thehindu.com",
}

TIER_2 = {
    "cnn.com", "cnbc.com", "abc.net.au", "cbc.ca",
    "politico.com", "politico.eu", "theatlantic.com",
    "foreignpolicy.com", "foreignaffairs.com",
    "chinadaily.com.cn", "globaltimes.cn", "japantimes.co.jp",
    "koreaherald.com", "koreajoongangdaily.joins.com",
    "timesofindia.indiatimes.com", "hindustantimes.com",
    "lemonde.fr", "elpais.com", "corriere.it", "spiegel.de",
    "marketwatch.com", "seekingalpha.com", "barrons.com",
}

TIER_3 = {
    "prnewswire.com", "businesswire.com", "globenewswire.com",
    "finanznachrichten.de", "marketscreener.com",
    "yahoo.com", "msn.com",
}


def get_source_tier(source_name: str) -> int:
    """Return credibility tier 1-4 for a source domain.  4 = unknown/unranked."""
    if not source_name:
        return 4
    domain = source_name.lower().strip()
    for t1 in TIER_1:
        if domain == t1 or domain.endswith("." + t1):
            return 1
    for t2 in TIER_2:
        if domain == t2 or domain.endswith("." + t2):
            return 2
    for t3 in TIER_3:
        if domain == t3 or domain.endswith("." + t3):
            return 3
    return 4


def rank_articles(articles: List[dict], max_per_tier: int = 5) -> List[dict]:
    """
    Rank and deduplicate articles for citation quality.

    Priority: Tier 1 first, then Tier 2, etc.
    Within each tier, sort by word_count desc (longer = more substance).
    Deduplicate by domain -- max 2 articles from same outlet.
    """
    for a in articles:
        a["tier"] = get_source_tier(a.get("source_name", ""))
    articles.sort(key=lambda a: (a["tier"], -(a.get("word_count") or 0)))

    domain_counts: dict = {}
    result: List[dict] = []
    for a in articles:
        domain = (a.get("source_name") or "unknown").lower().strip()
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if domain_counts[domain] <= 2:
            result.append(a)
    return result
