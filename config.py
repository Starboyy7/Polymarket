import os
import sys

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Rutas del token de sesión según plataforma (usado solo en Claude Code cloud)
_SESSION_TOKEN_CANDIDATES = [
    os.environ.get("CLAUDE_SESSION_INGRESS_TOKEN_FILE", ""),
    "/home/claude/.claude/remote/.session_ingress_token",          # Linux cloud
    os.path.expanduser("~/.claude/remote/.session_ingress_token"), # Linux/Mac local
]


def get_anthropic_client():
    """Retorna un cliente Anthropic autenticado.
    Prioridad: ANTHROPIC_API_KEY → token de sesión Claude Code.
    En Windows/local: configura ANTHROPIC_API_KEY en variables de entorno.
    """
    import anthropic
    if ANTHROPIC_API_KEY:
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    for path in _SESSION_TOKEN_CANDIDATES:
        if path and os.path.exists(path):
            try:
                token = open(path).read().strip()
                if token:
                    return anthropic.Anthropic(auth_token=token)
            except Exception:
                pass
    raise RuntimeError(
        "\n\n  ERROR  API key no encontrada.\n"
        "  Configura la variable de entorno ANTHROPIC_API_KEY:\n\n"
        "  Windows CMD:   set ANTHROPIC_API_KEY=sk-ant-...\n"
        "  Windows PS:    $env:ANTHROPIC_API_KEY='sk-ant-...'\n"
        "  Mac/Linux:     export ANTHROPIC_API_KEY=sk-ant-...\n\n"
        "  Obtén tu key en: https://console.anthropic.com\n"
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
