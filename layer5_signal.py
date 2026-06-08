"""Capa 5 — Señal Delta: P(simulada) vs P(Polymarket) con umbral mínimo."""
import logging
import uuid
from datetime import datetime
from typing import Optional

import config
from models import BayesianPrior, CrowdSignal, DeltaSignal, FilteredSignal, MonteCarloResult

logger = logging.getLogger(__name__)


def compute_delta_signal(
    signal: FilteredSignal,
    crowd: CrowdSignal,
    mc: MonteCarloResult,
    bayesian: BayesianPrior,
) -> Optional[DeltaSignal]:
    p_market    = signal.market.p_yes
    p_simulated = mc.p_mean
    delta       = p_simulated - p_market

    if abs(delta) < config.MIN_DELTA_THRESHOLD:
        logger.debug(
            f"Delta {delta:+.3f} below threshold {config.MIN_DELTA_THRESHOLD} "
            f"for '{signal.market.question[:50]}'"
        )
        return None

    confidence = (
        mc.confidence         * 0.50 +
        crowd.confidence      * 0.30 +
        signal.composite_score * 0.20
    )
    action = "BUY_YES" if delta > 0 else "BUY_NO"

    ds = DeltaSignal(
        market=signal.market,
        p_simulated=p_simulated,
        p_polymarket=p_market,
        delta=delta,
        confidence=confidence,
        signal_id=str(uuid.uuid4())[:8].upper(),
        timestamp=datetime.now(),
        filtered_signal=signal,
        crowd_signal=crowd,
        mc_result=mc,
        action=action,
    )

    logger.info(
        f"SIGNAL [{ds.signal_id}] {action} | "
        f"Δ={delta:+.3f} | P_mkt={p_market:.2f} P_sim={p_simulated:.2f} | "
        f"conf={confidence:.2f} | '{signal.market.question[:50]}'"
    )
    return ds
