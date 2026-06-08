"""Capa 4 — Monte Carlo: 10,000 simulaciones sobre distribución Beta parametrizada."""
import logging

import numpy as np

import config
from layer3_modeling import compute_combined_prior
from models import BayesianPrior, CrowdSignal, FilteredSignal, MonteCarloResult

logger = logging.getLogger(__name__)


def run_monte_carlo(
    signal: FilteredSignal,
    crowd: CrowdSignal,
    bayesian: BayesianPrior,
    n: int = None,
) -> MonteCarloResult:
    n = n or config.N_SIMULATIONS
    alpha, beta_p = compute_combined_prior(signal, crowd, bayesian)

    samples = np.random.beta(alpha, beta_p, n)

    # Add calibrated noise proportional to signal uncertainty
    noise_std = (1.0 - crowd.confidence) * 0.04
    samples = np.clip(samples + np.random.normal(0, noise_std, n), 0.01, 0.99)

    p_mean = float(np.mean(samples))
    p_std  = float(np.std(samples))
    p_5    = float(np.percentile(samples, 5))
    p_95   = float(np.percentile(samples, 95))

    # Confidence: narrower CI → higher confidence
    confidence = max(0.1, min(0.99, 1.0 - (p_95 - p_5) * 2.0))

    logger.info(
        f"Monte Carlo ({n:,} sims): P={p_mean:.3f} ± {p_std:.3f} "
        f"CI=[{p_5:.3f}, {p_95:.3f}] conf={confidence:.2f}"
    )
    return MonteCarloResult(p_mean=p_mean, p_std=p_std, p_5=p_5, p_95=p_95, confidence=confidence)
