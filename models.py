from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Market:
    id: str
    question: str
    category: str
    p_yes: float
    volume: float
    condition_id: str = ""
    description: str = ""
    url: str = ""


@dataclass
class NewsItem:
    title: str
    content: str
    source: str
    url: str
    published: datetime
    source_type: str = "rss"   # "gdelt" | "rss" | "reddit"


@dataclass
class FilteredSignal:
    news: NewsItem
    market: Market
    relevance_score: float
    novelty_score: float
    credibility_score: float
    composite_score: float = field(init=False)

    def __post_init__(self):
        self.composite_score = (
            self.relevance_score  * 0.40 +
            self.novelty_score    * 0.30 +
            self.credibility_score * 0.30
        )


@dataclass
class CrowdSignal:
    p_shift: float
    confidence: float
    direction: str          # "bullish" | "bearish" | "neutral"
    narrative: str
    p_adjusted: float = 0.0


@dataclass
class BayesianPrior:
    alpha: float
    beta: float
    category: str
    sample_size: int = 0


@dataclass
class MonteCarloResult:
    p_mean: float
    p_std: float
    p_5: float
    p_95: float
    confidence: float


@dataclass
class DeltaSignal:
    market: Market
    p_simulated: float
    p_polymarket: float
    delta: float
    confidence: float
    signal_id: str
    timestamp: datetime
    filtered_signal: FilteredSignal
    crowd_signal: CrowdSignal
    mc_result: MonteCarloResult
    action: str = "BUY_YES"   # "BUY_YES" | "BUY_NO"
