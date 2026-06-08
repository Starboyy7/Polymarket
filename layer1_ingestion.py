"""Capa 1 — Data Ingestion: Polymarket API, GDELT, RSS, Reddit."""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple

import requests

import config
from models import Market, NewsItem

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "PolymarketEcosystem/1.0"}


# ── Polymarket ────────────────────────────────────────────────────────────────

def fetch_markets(limit: int = 50) -> List[Market]:
    try:
        resp = requests.get(
            f"{config.POLYMARKET_GAMMA_API}/markets",
            params={"active": "true", "closed": "false", "limit": limit,
                    "order": "volume24hr", "ascending": "false"},
            headers=_HEADERS,
            timeout=12,
        )
        resp.raise_for_status()
        markets = []
        for m in resp.json():
            p_yes = _parse_price(m)
            if p_yes is None or not (0.01 < p_yes < 0.99):
                continue
            slug = m.get("slug", "")
            markets.append(Market(
                id=str(m.get("id", "")),
                question=m.get("question", "").strip(),
                category=m.get("category", "General") or "General",
                p_yes=p_yes,
                volume=float(m.get("volume", 0) or 0),
                condition_id=m.get("conditionId", ""),
                description=(m.get("description", "") or "")[:400],
                url=f"https://polymarket.com/event/{slug}" if slug else "",
            ))
        logger.info(f"Fetched {len(markets)} active markets from Polymarket")
        return markets
    except Exception as exc:
        logger.error(f"Polymarket fetch error: {exc}")
        return []


def _parse_price(m: dict) -> float | None:
    """Try several price fields that Polymarket API may return."""
    for field in ("outcomePrices", "outcomes"):
        raw = m.get(field)
        if isinstance(raw, list) and raw:
            try:
                val = float(raw[0])
                return val if val <= 1 else val / 100
            except (ValueError, TypeError):
                pass
    for field in ("lastTradePrice", "midpoint", "bestBid"):
        raw = m.get(field)
        if raw is not None:
            try:
                val = float(raw)
                return val if val <= 1 else val / 100
            except (ValueError, TypeError):
                pass
    return None


# ── GDELT ─────────────────────────────────────────────────────────────────────

def fetch_gdelt(query: str, max_records: int = 15) -> List[NewsItem]:
    try:
        resp = requests.get(
            config.GDELT_API,
            params={"query": query, "mode": "artlist", "maxrecords": max_records,
                    "format": "json", "timespan": "24h", "sort": "hybridrel"},
            timeout=12,
        )
        resp.raise_for_status()
        items = []
        for a in resp.json().get("articles", []):
            items.append(NewsItem(
                title=a.get("title", ""),
                content=a.get("title", ""),
                source=a.get("domain", "gdelt"),
                url=a.get("url", ""),
                published=datetime.now(),
                source_type="gdelt",
            ))
        logger.info(f"GDELT: {len(items)} articles for query '{query[:40]}'")
        return items
    except Exception as exc:
        logger.error(f"GDELT error: {exc}")
        return []


# ── RSS ───────────────────────────────────────────────────────────────────────

def fetch_rss(max_per_feed: int = 6) -> List[NewsItem]:
    items = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for url in config.RSS_FEEDS:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            # Support both RSS 2.0 and Atom
            entries = root.findall(".//item") or root.findall(".//atom:entry", ns)
            feed_title = (root.findtext("channel/title") or
                          root.findtext("atom:title", namespaces=ns) or url)
            for entry in entries[:max_per_feed]:
                title   = (entry.findtext("title") or
                           entry.findtext("atom:title", ns) or "")
                content = (entry.findtext("description") or
                           entry.findtext("atom:summary", ns) or title)
                link    = (entry.findtext("link") or
                           (entry.find("atom:link", ns) or {}).get("href", "") or "")  # type: ignore
                items.append(NewsItem(
                    title=title.strip(),
                    content=content.strip()[:400],
                    source=feed_title,
                    url=link,
                    published=datetime.now(),
                    source_type="rss",
                ))
        except Exception as exc:
            logger.error(f"RSS error {url}: {exc}")
    logger.info(f"RSS: {len(items)} items")
    return items


# ── Reddit ────────────────────────────────────────────────────────────────────

def fetch_reddit(max_per_sub: int = 5) -> List[NewsItem]:
    items = []
    for sub in config.REDDIT_SUBREDDITS:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/new.json",
                params={"limit": max_per_sub},
                headers=_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            for post in resp.json().get("data", {}).get("children", []):
                d = post.get("data", {})
                if d.get("score", 0) < 5:
                    continue
                items.append(NewsItem(
                    title=d.get("title", ""),
                    content=d.get("selftext", d.get("title", ""))[:400],
                    source=f"reddit/r/{sub}",
                    url=f"https://reddit.com{d.get('permalink', '')}",
                    published=datetime.now(),
                    source_type="reddit",
                ))
        except Exception as exc:
            logger.error(f"Reddit error r/{sub}: {exc}")
    logger.info(f"Reddit: {len(items)} posts")
    return items


# ── Orchestrator ──────────────────────────────────────────────────────────────

def ingest_all() -> Tuple[List[Market], List[NewsItem]]:
    markets = fetch_markets()
    if not markets:
        return [], []

    # Build GDELT query from top markets
    query_terms = " OR ".join(m.question[:40] for m in markets[:5])
    gdelt_news  = fetch_gdelt(query_terms)
    rss_news    = fetch_rss()
    reddit_news = fetch_reddit()

    all_news = gdelt_news + rss_news + reddit_news
    logger.info(f"Capa 1 complete: {len(markets)} markets | {len(all_news)} news items")
    return markets, all_news
