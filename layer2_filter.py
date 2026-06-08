"""Capa 2 — Filtrado LLM: relevancia, novedad, credibilidad."""
import json
import logging
from typing import List

import config
from models import FilteredSignal, Market, NewsItem

logger = logging.getLogger(__name__)
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = config.get_groq_client()
    return _client


def filter_signals(markets: List[Market], news_items: List[NewsItem]) -> List[FilteredSignal]:
    if not markets or not news_items:
        return []

    market_ctx = "\n".join(
        f"[{m.id}] {m.question} | P={m.p_yes:.2f} | cat={m.category}"
        for m in markets[:30]
    )
    market_map = {m.id: m for m in markets}

    signals: List[FilteredSignal] = []
    batch_size = 12

    for i in range(0, len(news_items), batch_size):
        batch = news_items[i : i + batch_size]
        news_ctx = "\n\n".join(
            f"[{j}] {n.source_type.upper()} | {n.source}\nTITLE: {n.title}\nCONTENT: {n.content[:250]}"
            for j, n in enumerate(batch)
        )

        prompt = f"""You are a Polymarket intelligence analyst.

ACTIVE MARKETS:
{market_ctx}

NEWS ITEMS:
{news_ctx}

For each news item relevant to any market, return a JSON array:
[
  {{
    "news_index": <int>,
    "market_id": "<id from market list>",
    "relevance_score": <0.0-1.0>,
    "novelty_score": <0.0-1.0>,
    "credibility_score": <0.0-1.0>
  }}
]

Rules:
- relevance_score: how directly this news affects that market's outcome
- novelty_score: 1.0 = completely new info not yet priced in, 0.0 = already known
- credibility_score: source reliability (reuters/bbc=0.9, reddit=0.4, unknown=0.3)
- Only include pairs where relevance_score >= 0.5
- One news item can match multiple markets
- Return [] if nothing is relevant

Return ONLY valid JSON, no explanation."""

        try:
            response = _get_client().chat.completions.create(
                model=config.GROQ_MODEL,
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            text = _extract_json(response.choices[0].message.content)
            results = json.loads(text)

            for r in results:
                idx = r.get("news_index", -1)
                mid = str(r.get("market_id", ""))
                if not (0 <= idx < len(batch)) or mid not in market_map:
                    continue
                rel = float(r.get("relevance_score", 0))
                cred = float(r.get("credibility_score", 0))
                if rel < config.MIN_RELEVANCE_SCORE or cred < config.MIN_CREDIBILITY_SCORE:
                    continue
                signals.append(FilteredSignal(
                    news=batch[idx],
                    market=market_map[mid],
                    relevance_score=rel,
                    novelty_score=float(r.get("novelty_score", 0.5)),
                    credibility_score=cred,
                ))

        except Exception as exc:
            logger.error(f"LLM filter error (batch {i}): {exc}")

    logger.info(f"Capa 2 complete: {len(signals)} signals from {len(news_items)} items")
    return signals


def _extract_json(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
