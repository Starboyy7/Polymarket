"""
Mercados históricos de Polymarket ya resueltos para backtesting.
Cada entrada refleja el estado del mercado en el momento de análisis
(precio y noticias disponibles en ese momento) + el outcome real.
"""
from datetime import datetime, timedelta
from models import Market, NewsItem

# Fecha base simulada: 3 meses atrás
T0 = datetime(2026, 3, 1)


def _days(d: int) -> datetime:
    return T0 + timedelta(days=d)


# ── Mercados históricos (ya resueltos) ────────────────────────────────────────

HISTORICAL_MARKETS = [
    # (market, news_at_time, actual_outcome)

    # 1. Fed cut rates Q1 2026 — RESOLVIÓ: YES
    (
        Market(id="h001", question="Will the Federal Reserve cut rates in Q1 2026?",
               category="Economics", p_yes=0.42, volume=2_100_000),
        [
            NewsItem(title="Fed minutes reveal growing consensus for rate cut amid disinflation",
                     content="FOMC minutes show majority of members discussed rate cut as appropriate given sustained progress toward 2% inflation target.",
                     source="wsj.com", url="", published=_days(0), source_type="rss"),
            NewsItem(title="CPI falls to 2.1% — lowest since 2021",
                     content="Consumer prices rose just 2.1% year-over-year in February, cementing expectations for Fed easing.",
                     source="reuters.com", url="", published=_days(1), source_type="gdelt"),
        ],
        "YES",
    ),

    # 2. Bitcoin $100k by March 2026 — RESOLVIÓ: NO
    (
        Market(id="h002", question="Will Bitcoin exceed $100,000 by March 31, 2026?",
               category="Crypto", p_yes=0.55, volume=3_800_000),
        [
            NewsItem(title="Bitcoin ETF sees massive $1.5B outflow amid regulatory uncertainty",
                     content="Spot Bitcoin ETFs recorded their largest single-day outflow as SEC signals new scrutiny of crypto markets.",
                     source="coindesk.com", url="", published=_days(0), source_type="gdelt"),
            NewsItem(title="Crypto market drops 18% as macro risk sentiment deteriorates",
                     content="Risk-off sentiment dominates as equity volatility spikes and institutional crypto positions are reduced.",
                     source="bloomberg.com", url="", published=_days(2), source_type="rss"),
        ],
        "NO",
    ),

    # 3. Trump tariff EO in Q1 2026 — RESOLVIÓ: YES
    (
        Market(id="h003", question="Will Trump sign an executive order expanding tariffs in Q1 2026?",
               category="Politics", p_yes=0.61, volume=1_450_000),
        [
            NewsItem(title="Trump announces 'Liberation Day 2.0' tariff package next week",
                     content="The White House confirmed a broad executive order targeting imports from 30 countries is being finalized.",
                     source="politico.com", url="", published=_days(0), source_type="rss"),
            NewsItem(title="Trade advisors brief Congress on sweeping new tariff framework",
                     content="Senior trade officials briefed congressional leaders on a comprehensive tariff expansion set for executive action.",
                     source="reuters.com", url="", published=_days(1), source_type="gdelt"),
        ],
        "YES",
    ),

    # 4. US unemployment > 4.5% Q1 2026 — RESOLVIÓ: NO
    (
        Market(id="h004", question="Will US unemployment rate exceed 4.5% in Q1 2026?",
               category="Economics", p_yes=0.31, volume=780_000),
        [
            NewsItem(title="Jobs report beats expectations: 210K jobs added in February",
                     content="Nonfarm payrolls rose 210,000 in February, above the 170,000 consensus estimate, with unemployment holding at 4.1%.",
                     source="bls.gov", url="", published=_days(0), source_type="rss"),
            NewsItem(title="Fed Beige Book shows labor market remains resilient across regions",
                     content="The Fed's Beige Book describes labor market conditions as 'solid' with limited signs of deterioration.",
                     source="federalreserve.gov", url="", published=_days(3), source_type="gdelt"),
        ],
        "NO",
    ),

    # 5. S&P 500 > 5800 by Feb 2026 — RESOLVIÓ: YES
    (
        Market(id="h005", question="Will the S&P 500 close above 5800 before March 1, 2026?",
               category="Economics", p_yes=0.48, volume=920_000),
        [
            NewsItem(title="Tech megacaps deliver blowout Q4 earnings, S&P surges 2.3%",
                     content="Alphabet, Microsoft and Meta beat earnings estimates by wide margins, propelling the S&P 500 to 5,740.",
                     source="wsj.com", url="", published=_days(0), source_type="rss"),
            NewsItem(title="Fed pivot expectations fuel equity rally; S&P approaches all-time high",
                     content="Rate cut expectations and strong corporate earnings push equities higher with the S&P within 1% of record levels.",
                     source="ft.com", url="", published=_days(2), source_type="gdelt"),
        ],
        "YES",
    ),

    # 6. Ethereum ETF staking approval by Q1 2026 — RESOLVIÓ: NO
    (
        Market(id="h006", question="Will the SEC approve Ethereum ETF staking by March 2026?",
               category="Crypto", p_yes=0.38, volume=560_000),
        [
            NewsItem(title="SEC delays Ethereum staking ETF decision for 90 days",
                     content="The Securities and Exchange Commission extended its review period for Ethereum staking ETF applications, citing need for further analysis.",
                     source="sec.gov", url="", published=_days(0), source_type="rss"),
            NewsItem(title="Industry groups push back on SEC's cautious staking stance",
                     content="Crypto lobbying groups criticized the SEC's delay on staking-enabled ETFs as excessive regulatory caution.",
                     source="coindesk.com", url="", published=_days(4), source_type="reddit"),
        ],
        "NO",
    ),

    # 7. Zelensky visits White House Q1 2026 — RESOLVIÓ: YES
    (
        Market(id="h007", question="Will Zelensky visit the White House in Q1 2026?",
               category="Politics", p_yes=0.52, volume=340_000),
        [
            NewsItem(title="Ukraine peace talks gain momentum; Zelensky Washington visit being planned",
                     content="Diplomatic sources confirm discussions underway for a Zelensky-Trump summit at the White House as ceasefire negotiations progress.",
                     source="axios.com", url="", published=_days(0), source_type="rss"),
            NewsItem(title="State Department confirms high-level Ukraine diplomatic visit imminent",
                     content="The State Department said a 'significant diplomatic engagement' with Ukraine is expected in the coming weeks.",
                     source="state.gov", url="", published=_days(2), source_type="gdelt"),
        ],
        "YES",
    ),

    # 8. Oil price > $90 by end of Q1 2026 — RESOLVIÓ: NO
    (
        Market(id="h008", question="Will WTI crude oil exceed $90/barrel by March 31, 2026?",
               category="Economics", p_yes=0.29, volume=670_000),
        [
            NewsItem(title="OPEC+ signals production increase amid demand slowdown concerns",
                     content="OPEC+ members agreed to gradually increase output by 400,000 barrels/day, citing global demand softness.",
                     source="reuters.com", url="", published=_days(0), source_type="rss"),
            NewsItem(title="IEA lowers 2026 oil demand forecast citing China slowdown",
                     content="The International Energy Agency cut its global oil demand growth forecast for 2026 to 800,000 b/d, below prior estimates.",
                     source="iea.org", url="", published=_days(3), source_type="gdelt"),
        ],
        "NO",
    ),
]
