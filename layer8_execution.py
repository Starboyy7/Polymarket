"""Capa 8 — Ejecución: paper trading engine con Kelly sizing y tracking de P&L."""
import sqlite3
import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import config
from models import DeltaSignal

logger = logging.getLogger(__name__)

PAPER_DB = "data/paper_trading.db"
STARTING_CAPITAL = 1_000.0   # USDC virtual
KELLY_FRACTION   = 0.25      # fracción de Kelly (conservador)
MAX_POSITION_PCT = 0.05      # máximo 5% del portafolio por posición
MIN_CONFIDENCE   = 0.30      # confianza mínima para abrir orden


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class PaperOrder:
    order_id: str
    signal_id: str
    market_id: str
    market_question: str
    category: str
    action: str              # BUY_YES | BUY_NO
    entry_price: float       # p_yes al momento de la señal
    shares: float            # contratos comprados
    usdc_invested: float     # $ USDC invertidos
    portfolio_at_entry: float
    p_simulated: float
    delta: float
    confidence: float
    crowd_narrative: str
    timestamp: datetime
    status: str = "open"     # open | resolved | expired
    exit_price: float = 0.0  # 0.0 o 1.0 al resolver
    pnl_usdc: float = 0.0
    pnl_pct: float = 0.0
    outcome: str = ""        # YES | NO
    resolved_at: Optional[datetime] = None


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    cash: float
    open_positions: int
    total_invested: float
    unrealized_pnl: float
    realized_pnl: float
    total_value: float
    roi_pct: float


# ── Database ──────────────────────────────────────────────────────────────────

@contextmanager
def _db():
    conn = sqlite3.connect(PAPER_DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize():
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS paper_orders (
                order_id          TEXT PRIMARY KEY,
                signal_id         TEXT,
                market_id         TEXT,
                market_question   TEXT,
                category          TEXT,
                action            TEXT,
                entry_price       REAL,
                shares            REAL,
                usdc_invested     REAL,
                portfolio_at_entry REAL,
                p_simulated       REAL,
                delta             REAL,
                confidence        REAL,
                crowd_narrative   TEXT,
                timestamp         TEXT,
                status            TEXT DEFAULT 'open',
                exit_price        REAL DEFAULT 0.0,
                pnl_usdc          REAL DEFAULT 0.0,
                pnl_pct           REAL DEFAULT 0.0,
                outcome           TEXT DEFAULT '',
                resolved_at       TEXT
            );

            CREATE TABLE IF NOT EXISTS portfolio_state (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT,
                cash         REAL,
                realized_pnl REAL
            );
        """)
        conn.execute(
            "INSERT OR IGNORE INTO portfolio_state (timestamp, cash, realized_pnl) VALUES (datetime('now'), ?, 0.0)",
            (STARTING_CAPITAL,),
        )
    logger.info(f"Paper trading DB initialized (capital: ${STARTING_CAPITAL:,.0f} USDC)")


# ── Portfolio helpers ─────────────────────────────────────────────────────────

def _get_cash() -> float:
    with _db() as conn:
        row = conn.execute(
            "SELECT cash, realized_pnl FROM portfolio_state ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row["cash"] if row else STARTING_CAPITAL


def _set_cash(cash: float, realized_pnl_delta: float = 0.0):
    with _db() as conn:
        last = conn.execute(
            "SELECT realized_pnl FROM portfolio_state ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev_pnl = last["realized_pnl"] if last else 0.0
        conn.execute(
            "INSERT INTO portfolio_state (timestamp, cash, realized_pnl) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), cash, prev_pnl + realized_pnl_delta),
        )


def get_open_orders() -> List[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM paper_orders WHERE status='open' ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_orders() -> List[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM paper_orders ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(r) for r in rows]


# ── Kelly Criterion ───────────────────────────────────────────────────────────

def kelly_size(p_win: float, p_market: float, portfolio_value: float) -> float:
    """
    Kelly criterion para mercados binarios.
    p_win    = nuestra probabilidad estimada de ganar
    p_market = precio del mercado (también la probabilidad implícita)
    Retorna: USDC a invertir
    """
    if p_market <= 0 or p_market >= 1:
        return 0.0
    b = (1.0 / p_market) - 1.0   # odds netas (payout si gana)
    q = 1.0 - p_win
    kelly = (b * p_win - q) / b
    kelly = max(0.0, kelly) * KELLY_FRACTION   # Kelly fraccionado
    max_bet = portfolio_value * MAX_POSITION_PCT
    return min(kelly * portfolio_value, max_bet)


# ── Core: abrir orden ─────────────────────────────────────────────────────────

def open_paper_order(signal: DeltaSignal) -> Optional[PaperOrder]:
    if signal.confidence < MIN_CONFIDENCE:
        logger.info(
            f"Señal {signal.signal_id} ignorada: confianza {signal.confidence:.2f} < {MIN_CONFIDENCE}"
        )
        return None

    cash = _get_cash()
    # Para BUY_YES: queremos p_yes suba → p_win = p_simulated
    # Para BUY_NO:  queremos p_yes baje → p_win = 1 - p_simulated
    if signal.action == "BUY_YES":
        entry_price = signal.p_polymarket
        p_win       = signal.p_simulated
    else:
        entry_price = 1.0 - signal.p_polymarket
        p_win       = 1.0 - signal.p_simulated

    portfolio_value = cash   # simplificado: no contabilizamos unrealized aquí
    usdc_to_invest  = kelly_size(p_win, entry_price, portfolio_value)

    if usdc_to_invest < 1.0:
        logger.info(f"Señal {signal.signal_id}: Kelly sizing < $1 USDC, omitida")
        return None

    if usdc_to_invest > cash:
        logger.warning(f"Sin suficiente cash (${cash:.2f}). Reduciendo posición.")
        usdc_to_invest = cash * MAX_POSITION_PCT

    shares = usdc_to_invest / entry_price
    order = PaperOrder(
        order_id=str(uuid.uuid4())[:8].upper(),
        signal_id=signal.signal_id,
        market_id=signal.market.id,
        market_question=signal.market.question,
        category=signal.market.category,
        action=signal.action,
        entry_price=entry_price,
        shares=shares,
        usdc_invested=usdc_to_invest,
        portfolio_at_entry=portfolio_value,
        p_simulated=signal.p_simulated,
        delta=signal.delta,
        confidence=signal.confidence,
        crowd_narrative=signal.crowd_signal.narrative,
        timestamp=signal.timestamp,
    )

    new_cash = cash - usdc_to_invest
    _set_cash(new_cash)

    with _db() as conn:
        conn.execute("""
            INSERT INTO paper_orders (
                order_id, signal_id, market_id, market_question, category,
                action, entry_price, shares, usdc_invested, portfolio_at_entry,
                p_simulated, delta, confidence, crowd_narrative, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order.order_id, order.signal_id, order.market_id, order.market_question,
            order.category, order.action, order.entry_price, order.shares,
            order.usdc_invested, order.portfolio_at_entry, order.p_simulated,
            order.delta, order.confidence, order.crowd_narrative,
            order.timestamp.isoformat(),
        ))

    logger.info(
        f"PAPER ORDER [{order.order_id}] {order.action} | "
        f"${usdc_to_invest:.2f} USDC @ {entry_price:.3f} | "
        f"{shares:.2f} shares | cash restante: ${new_cash:.2f}"
    )
    return order


# ── Core: resolver orden ──────────────────────────────────────────────────────

def resolve_paper_order(order_id: str, outcome: str):
    """
    outcome: 'YES' o 'NO'
    BUY_YES gana si outcome=YES  → exit_price = 1.0
    BUY_NO  gana si outcome=NO   → exit_price = 1.0
    """
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM paper_orders WHERE order_id=?", (order_id,)
        ).fetchone()
        if not row:
            logger.error(f"Orden {order_id} no encontrada")
            return
        order = dict(row)

    won = (order["action"] == "BUY_YES" and outcome == "YES") or \
          (order["action"] == "BUY_NO"  and outcome == "NO")

    exit_price = 1.0 if won else 0.0
    pnl_usdc   = order["shares"] * exit_price - order["usdc_invested"]
    pnl_pct    = (pnl_usdc / order["usdc_invested"]) * 100

    cash = _get_cash()
    new_cash = cash + order["shares"] * exit_price
    _set_cash(new_cash, realized_pnl_delta=pnl_usdc)

    with _db() as conn:
        conn.execute("""
            UPDATE paper_orders
            SET status='resolved', exit_price=?, pnl_usdc=?, pnl_pct=?,
                outcome=?, resolved_at=?
            WHERE order_id=?
        """, (exit_price, pnl_usdc, pnl_pct, outcome,
              datetime.now().isoformat(), order_id))

    result = "✓ GANADA" if won else "✗ PERDIDA"
    logger.info(
        f"RESOLVED [{order_id}] {result} | outcome={outcome} | "
        f"P&L: ${pnl_usdc:+.2f} ({pnl_pct:+.1f}%) | cash: ${new_cash:.2f}"
    )


# ── Performance report ────────────────────────────────────────────────────────

def performance_report() -> dict:
    orders = get_all_orders()
    resolved = [o for o in orders if o["status"] == "resolved"]
    open_ord = [o for o in orders if o["status"] == "open"]

    cash = _get_cash()
    total_invested_open = sum(o["usdc_invested"] for o in open_ord)

    if not resolved:
        return {
            "total_orders": len(orders),
            "open": len(open_ord),
            "resolved": 0,
            "win_rate": None,
            "total_pnl": 0.0,
            "roi_pct": 0.0,
            "cash": cash,
        }

    wins    = [o for o in resolved if o["pnl_usdc"] > 0]
    losses  = [o for o in resolved if o["pnl_usdc"] <= 0]
    total_pnl = sum(o["pnl_usdc"] for o in resolved)
    total_wagered = sum(o["usdc_invested"] for o in resolved)
    win_rate = len(wins) / len(resolved) if resolved else 0
    roi      = (total_pnl / total_wagered * 100) if total_wagered else 0

    avg_win  = sum(o["pnl_usdc"] for o in wins)  / len(wins)  if wins   else 0
    avg_loss = sum(o["pnl_usdc"] for o in losses) / len(losses) if losses else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    return {
        "total_orders":   len(orders),
        "open":           len(open_ord),
        "resolved":       len(resolved),
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate":       win_rate,
        "total_pnl":      total_pnl,
        "total_wagered":  total_wagered,
        "roi_pct":        roi,
        "avg_win":        avg_win,
        "avg_loss":       avg_loss,
        "profit_factor":  profit_factor,
        "cash":           cash,
        "portfolio_value": cash + total_invested_open,
        "starting_capital": STARTING_CAPITAL,
    }
