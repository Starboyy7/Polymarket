import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_SESSION_TOKEN_FILE = os.environ.get(
    "CLAUDE_SESSION_INGRESS_TOKEN_FILE",
    "/home/claude/.claude/remote/.session_ingress_token",
)
CLAUDE_MODEL = "claude-sonnet-4-6"


def get_anthropic_client():
    """Returns an authenticated Anthropic client using API key or session token."""
    import anthropic
    if ANTHROPIC_API_KEY:
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        token = open(CLAUDE_SESSION_TOKEN_FILE).read().strip()
        return anthropic.Anthropic(auth_token=token)
    except Exception:
        raise RuntimeError(
            "No se encontró ANTHROPIC_API_KEY ni token de sesión. "
            "Configura la variable ANTHROPIC_API_KEY."
        )

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
