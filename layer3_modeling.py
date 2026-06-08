"""Capa 3 — Modelado: simulación de crowd (Claude) + base rates bayesianas."""
import json
import logging
from typing import Dict, Tuple

import anthropic

import config
from models import BayesianPrior, CrowdSignal, FilteredSignal

logger = logging.getLogger(__name__)
_client = config.get_anthropic_client()

_DEFAULT_PRIORS: Dict[str, Dict[str, float]] = {
    "Politics":   {"alpha": 3.0, "beta": 2.0},
    "Sports":     {"alpha": 2.5, "beta": 2.5},
    "Crypto":     {"alpha": 2.0, "beta": 3.0},
    "Economics":  {"alpha": 3.0, "beta": 2.0},
    "Science":    {"alpha": 3.5, "beta": 1.5},
    "General":    {"alpha": 2.5, "beta": 2.5},
}


# ── 3A: Claude Crowd Simulator ────────────────────────────────────────────────

def simulate_crowd_reaction(signal: FilteredSignal) -> CrowdSignal:
    """Claude simulates Twitter/Reddit crowd reaction to a filtered news signal."""
    prompt = f"""You are simulating prediction market participants and social media agents reacting to news.

MARKET: {signal.market.question}
CURRENT PROBABILITY: {signal.market.p_yes:.2f} ({signal.market.p_yes * 100:.1f}%)
CATEGORY: {signal.market.category}

NEWS:
Title: {signal.news.title}
Source: {signal.news.source} ({signal.news.source_type})
Content: {signal.news.content[:400]}

Signal scores — Relevance: {signal.relevance_score:.2f} | Novelty: {signal.novelty_score:.2f} | Credibility: {signal.credibility_score:.2f}

Simulate how Twitter and Reddit prediction market participants react over the next 24-72 hours.
Consider: initial sentiment surge, contrarian pushback, whale positioning, information cascade, narrative decay.

Respond ONLY with this JSON:
{{
  "p_shift": <float -0.30 to +0.30>,
  "confidence": <float 0.0-1.0>,
  "direction": "bullish" or "bearish" or "neutral",
  "narrative": "<2 sentences describing the crowd reaction arc>"
}}"""

    try:
        resp = _client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(_extract_json(resp.content[0].text))
        p_shift = max(-0.30, min(0.30, float(data.get("p_shift", 0.0))))
        p_adj   = max(0.01, min(0.99, signal.market.p_yes + p_shift))
        return CrowdSignal(
            p_shift=p_shift,
            confidence=float(data.get("confidence", 0.5)),
            direction=data.get("direction", "neutral"),
            narrative=data.get("narrative", ""),
            p_adjusted=p_adj,
        )
    except Exception as exc:
        logger.error(f"Crowd simulation error: {exc}")
        return CrowdSignal(
            p_shift=0.0, confidence=0.3, direction="neutral",
            narrative="Simulation unavailable.",
            p_adjusted=signal.market.p_yes,
        )


# ── 3B: Bayesian Base Rates ───────────────────────────────────────────────────

def get_bayesian_prior(category: str, feedback_weights: Dict[str, float]) -> BayesianPrior:
    """Return Beta distribution prior for the market category, adjusted by feedback."""
    prior = _DEFAULT_PRIORS.get(category, _DEFAULT_PRIORS["General"]).copy()
    weight = feedback_weights.get(category, 1.0)
    return BayesianPrior(
        alpha=prior["alpha"] * weight,
        beta=prior["beta"],
        category=category,
    )


# ── Combined prior for Monte Carlo ────────────────────────────────────────────

def compute_combined_prior(
    signal: FilteredSignal,
    crowd: CrowdSignal,
    bayesian: BayesianPrior,
) -> Tuple[float, float]:
    """Blend crowd signal + Bayesian prior into Beta(α, β) parameters."""
    crowd_weight = signal.composite_score * crowd.confidence
    prior_mean   = bayesian.alpha / (bayesian.alpha + bayesian.beta)
    combined_p   = max(0.01, min(0.99, crowd_weight * crowd.p_adjusted + (1 - crowd_weight) * prior_mean))
    concentration = (bayesian.alpha + bayesian.beta) + 5 * crowd_weight
    return combined_p * concentration, (1 - combined_p) * concentration


def _extract_json(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
