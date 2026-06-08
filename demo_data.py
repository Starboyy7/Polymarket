"""Datos de muestra para validar el pipeline sin acceso a red."""
from datetime import datetime
from models import Market, NewsItem


MARKETS = [
    Market(id="m001", question="Will the Federal Reserve cut rates before Q4 2026?",
           category="Economics", p_yes=0.62, volume=1_200_000),
    Market(id="m002", question="Will Bitcoin reach $150,000 by end of 2026?",
           category="Crypto", p_yes=0.38, volume=850_000),
    Market(id="m003", question="Will the US unemployment rate exceed 5% in 2026?",
           category="Economics", p_yes=0.29, volume=430_000),
    Market(id="m004", question="Will Donald Trump sign a new executive order on tariffs in June 2026?",
           category="Politics", p_yes=0.71, volume=670_000),
    Market(id="m005", question="Will the S&P 500 hit 6500 before July 2026?",
           category="Economics", p_yes=0.44, volume=320_000),
]

NEWS = [
    NewsItem(
        title="Federal Reserve signals possible rate cut as labor market softens",
        content="Fed officials indicated openness to rate reductions after new CPI data showed inflation trending toward the 2% target amid rising unemployment.",
        source="reuters.com", url="https://reuters.com/1", published=datetime.now(), source_type="rss",
    ),
    NewsItem(
        title="Bitcoin ETF inflows hit record $2B in a single day",
        content="Spot Bitcoin ETFs saw unprecedented inflows following renewed institutional interest and positive macro signals from the Federal Reserve.",
        source="coindesk.com", url="https://coindesk.com/1", published=datetime.now(), source_type="gdelt",
    ),
    NewsItem(
        title="US jobless claims unexpectedly surge to 8-month high",
        content="Weekly initial jobless claims rose sharply to 245,000, the highest since October 2025, raising concerns about labor market weakness.",
        source="bloomberg.com", url="https://bloomberg.com/1", published=datetime.now(), source_type="rss",
    ),
    NewsItem(
        title="White House hints at broader tariff executive action this month",
        content="Senior administration officials say a sweeping executive order on trade tariffs is being drafted and could be signed before month's end.",
        source="politico.com", url="https://politico.com/1", published=datetime.now(), source_type="reddit",
    ),
    NewsItem(
        title="Markets rally on strong tech earnings, S&P approaches 6400",
        content="Equity markets surged after better-than-expected earnings from major tech companies, pushing the S&P 500 to within 1.5% of the 6500 milestone.",
        source="wsj.com", url="https://wsj.com/1", published=datetime.now(), source_type="rss",
    ),
    NewsItem(
        title="Eurovision 2026 final expected record viewership",
        content="Broadcasters anticipate over 200 million viewers for this year's Eurovision Song Contest final in Stockholm.",
        source="bbc.com", url="https://bbc.com/1", published=datetime.now(), source_type="rss",
    ),
]
