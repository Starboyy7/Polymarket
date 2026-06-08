"""Capa 7 — Feedback loop: hit rate por categoría + re-weighting automático."""
import logging
from datetime import datetime
from typing import Dict

import layer6_registry as registry

logger = logging.getLogger(__name__)

CATEGORIES = ["Politics", "Sports", "Crypto", "Economics", "Science", "General"]


def compute_hit_rates() -> Dict[str, dict]:
    stats: Dict[str, dict] = {}
    for cat in CATEGORIES:
        resolved = registry.get_resolved(category=cat)
        total    = len(resolved)
        correct  = sum(1 for p in resolved if p.get("correct") == 1)
        hit_rate = correct / total if total else 0.5
        # Weight in [0.5, 1.5]: rewarded above 50% hit rate, penalized below
        weight   = 0.5 + hit_rate
        stats[cat] = {
            "hit_rate":         hit_rate,
            "total":            total,
            "correct":          correct,
            "weight_multiplier": weight,
        }
    return stats


def _persist_weights(stats: Dict[str, dict]):
    with registry._db() as conn:
        for cat, d in stats.items():
            conn.execute("""
                INSERT OR REPLACE INTO feedback_weights
                (category, hit_rate, total_predictions, correct_predictions, weight_multiplier, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cat, d["hit_rate"], d["total"], d["correct"], d["weight_multiplier"], datetime.now().isoformat()))


def get_weights() -> Dict[str, float]:
    """Return current weight_multiplier per category (used by Capa 3)."""
    with registry._db() as conn:
        rows = conn.execute("SELECT category, weight_multiplier FROM feedback_weights").fetchall()
    if not rows:
        return {cat: 1.0 for cat in CATEGORIES}
    return {row["category"]: row["weight_multiplier"] for row in rows}


def run() -> Dict[str, dict]:
    """Full feedback cycle: compute → persist → log."""
    stats = compute_hit_rates()
    _persist_weights(stats)
    logger.info("Feedback loop update:")
    for cat, d in stats.items():
        logger.info(
            f"  {cat:12s} hit={d['hit_rate']:.2f} "
            f"({d['correct']}/{d['total']}) weight={d['weight_multiplier']:.2f}"
        )
    return stats
