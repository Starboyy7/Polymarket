"""Capa 6 — Registro de predicciones: timestamp + señal + resultado real."""
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

import config
from models import DeltaSignal

logger = logging.getLogger(__name__)


@contextmanager
def _db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize():
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS predictions (
                signal_id       TEXT PRIMARY KEY,
                timestamp       TEXT NOT NULL,
                market_id       TEXT NOT NULL,
                market_question TEXT NOT NULL,
                market_category TEXT NOT NULL,
                p_polymarket    REAL NOT NULL,
                p_simulated     REAL NOT NULL,
                delta           REAL NOT NULL,
                confidence      REAL NOT NULL,
                action          TEXT NOT NULL,
                crowd_narrative TEXT,
                news_title      TEXT,
                news_source     TEXT,
                outcome         TEXT,
                resolved_at     TEXT,
                correct         INTEGER
            );

            CREATE TABLE IF NOT EXISTS feedback_weights (
                category            TEXT PRIMARY KEY,
                hit_rate            REAL    DEFAULT 0.5,
                total_predictions   INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                weight_multiplier   REAL    DEFAULT 1.0,
                last_updated        TEXT
            );
        """)
    logger.info("Database initialized")


def save_signal(signal: DeltaSignal):
    with _db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO predictions (
                signal_id, timestamp, market_id, market_question, market_category,
                p_polymarket, p_simulated, delta, confidence, action,
                crowd_narrative, news_title, news_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.signal_id,
            signal.timestamp.isoformat(),
            signal.market.id,
            signal.market.question,
            signal.market.category,
            signal.p_polymarket,
            signal.p_simulated,
            signal.delta,
            signal.confidence,
            signal.action,
            signal.crowd_signal.narrative,
            signal.filtered_signal.news.title,
            signal.filtered_signal.news.source,
        ))
    logger.info(f"Signal {signal.signal_id} saved to registry")


def resolve(signal_id: str, outcome: str, correct: bool):
    """Call this when a market resolves to record the actual outcome."""
    with _db() as conn:
        conn.execute("""
            UPDATE predictions
            SET outcome=?, resolved_at=?, correct=?
            WHERE signal_id=?
        """, (outcome, datetime.now().isoformat(), int(correct), signal_id))
    logger.info(f"Signal {signal_id} resolved — correct={correct}")


def get_pending() -> List[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE outcome IS NULL ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_resolved(category: Optional[str] = None) -> List[dict]:
    with _db() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM predictions WHERE outcome IS NOT NULL AND market_category=? ORDER BY resolved_at DESC",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM predictions WHERE outcome IS NOT NULL ORDER BY resolved_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]
