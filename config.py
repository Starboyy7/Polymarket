import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"


def get_groq_client():
    """Retorna un cliente Groq autenticado.
    Configura GROQ_API_KEY en variables de entorno.
    Obtén tu key gratis en: https://console.groq.com
    """
    from groq import Groq
    if not GROQ_API_KEY:
        raise RuntimeError(
            "\n\n  ERROR  GROQ_API_KEY no encontrada.\n"
            "  Configura la variable de entorno GROQ_API_KEY:\n\n"
            "  Windows CMD:   set GROQ_API_KEY=gsk_...\n"
            "  Windows PS:    $env:GROQ_API_KEY='gsk_...'\n"
            "  Mac/Linux:     export GROQ_API_KEY=gsk_...\n\n"
            "  Obtén tu key gratis en: https://console.groq.com\n"
        )
    return Groq(api_key=GROQ_API_KEY)


POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB_API  = "https://clob.polymarket.com"
GDELT_API            = "https://api.gdeltproject.org/api/v2/doc/doc"

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
]
REDDIT_SUBREDDITS = ["politics", "worldnews", "economics", "CryptoCurrency", "geopolitics"]

# Capa 2
MIN_RELEVANCE_SCORE   = 0.55
MIN_CREDIBILITY_SCORE = 0.45

# Capa 4
N_SIMULATIONS = 10_000

# Capa 5
MIN_DELTA_THRESHOLD = 0.07   # 7 percentage points

DB_PATH = "data/registry.db"
