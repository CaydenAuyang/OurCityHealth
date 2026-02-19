"""
Event Deduplication

Groups raw GDELT events that describe the same real-world happening so the
LLM receives consolidated, multi-source intelligence rather than duplicate
headlines.

Grouping criteria (ALL must match):
  - Same CAMEO root code (first 2 digits of event_code)
  - At least one actor in common
  - Within 2 calendar days of each other
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel

from .source_ranker import get_source_tier


class DedupedEvent(BaseModel):
    """A consolidated real-world event backed by multiple raw GDELT rows."""
    date_range: str
    primary_description: str
    event_code: str
    event_description: str
    actors: List[str]
    avg_goldstein: float
    source_count: int
    source_urls: List[str]
    total_mentions: int


def _cameo_root(code: Optional[str]) -> str:
    if not code:
        return ""
    return str(code).zfill(3)[:2]


def _actors_set(ev: dict) -> set:
    result = set()
    a1 = (ev.get("actor1") or "").strip()
    a2 = (ev.get("actor2") or "").strip()
    if a1:
        result.add(a1.lower())
    if a2:
        result.add(a2.lower())
    return result


def _parse_date(d) -> Optional[date]:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        try:
            return date.fromisoformat(d)
        except ValueError:
            return None
    return None


def _format_date_range(dates: List[date]) -> str:
    if not dates:
        return ""
    mn = min(dates)
    mx = max(dates)
    if mn == mx:
        return mn.strftime("%b %d, %Y")
    if mn.year == mx.year and mn.month == mx.month:
        return f"{mn.strftime('%b %d')}-{mx.day}, {mn.year}"
    return f"{mn.strftime('%b %d, %Y')} - {mx.strftime('%b %d, %Y')}"


def deduplicate_events(events: List[dict]) -> List[DedupedEvent]:
    """
    Group events that likely describe the same real-world happening.

    Each event dict should have: event_date, event_code, actor1, actor2,
    goldstein_scale, num_mentions, source_url, event_description.

    Returns list sorted by total_mentions desc.
    """
    # Sort by date
    sorted_events = sorted(
        events,
        key=lambda e: _parse_date(e.get("event_date")) or date.min,
    )

    groups: List[List[dict]] = []

    for ev in sorted_events:
        ev_root = _cameo_root(ev.get("event_code"))
        ev_actors = _actors_set(ev)
        ev_date = _parse_date(ev.get("event_date"))
        if not ev_date:
            continue

        merged = False
        for grp in groups:
            rep = grp[0]
            rep_root = _cameo_root(rep.get("event_code"))
            rep_date = _parse_date(rep.get("event_date"))
            rep_actors = set()
            for g in grp:
                rep_actors |= _actors_set(g)
            latest_date = max(
                _parse_date(g.get("event_date")) or date.min for g in grp
            )

            if (
                ev_root == rep_root
                and ev_actors & rep_actors
                and abs((ev_date - latest_date).days) <= 2
            ):
                grp.append(ev)
                merged = True
                break

        if not merged:
            groups.append([ev])

    result: List[DedupedEvent] = []
    for grp in groups:
        dates = [_parse_date(e.get("event_date")) for e in grp]
        dates = [d for d in dates if d is not None]
        all_actors: set = set()
        total_gs = 0.0
        total_mentions = 0
        urls: List[str] = []

        best = grp[0]
        best_score = (abs(best.get("goldstein_scale") or 0)) * max(best.get("num_mentions") or 1, 1)

        for e in grp:
            all_actors |= _actors_set(e)
            total_gs += e.get("goldstein_scale") or 0.0
            total_mentions += e.get("num_mentions") or 0
            url = e.get("source_url")
            if url and url not in urls:
                urls.append(url)
            impact = abs(e.get("goldstein_scale") or 0) * max(e.get("num_mentions") or 1, 1)
            if impact > best_score:
                best = e
                best_score = impact

        # Rank URLs by source credibility
        url_tiers = [(u, get_source_tier(u)) for u in urls]
        url_tiers.sort(key=lambda x: x[1])
        ranked_urls = [u for u, _ in url_tiers]

        actors_list = sorted(a.title() for a in all_actors if a and a != "unknown")

        result.append(DedupedEvent(
            date_range=_format_date_range(dates),
            primary_description=best.get("event_description") or "",
            event_code=best.get("event_code") or "",
            event_description=best.get("event_description") or "",
            actors=actors_list,
            avg_goldstein=total_gs / len(grp) if grp else 0.0,
            source_count=len(ranked_urls),
            source_urls=ranked_urls[:5],
            total_mentions=total_mentions,
        ))

    result.sort(key=lambda e: e.total_mentions, reverse=True)
    return result
