"""
Configuration for AI Finance News Agent.
"""

import os
from typing import Final

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# ---------------------------------------------------------
# RSS FEEDS
# ---------------------------------------------------------

RSS_FEEDS: Final[dict[str, str]] = {
    "Economic Times Markets":
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",

    "Moneycontrol Business":
        "https://www.moneycontrol.com/rss/business.xml",

    "Reuters Business":
        "https://feeds.reuters.com/reuters/businessNews",

    "Bloomberg Markets":
        "https://feeds.bloomberg.com/markets/news.rss",

    "CNBC TV18 Markets":
        "https://www.moneycontrol.com/rss/marketreports.xml",
}


# ---------------------------------------------------------
# NEWS SETTINGS
# ---------------------------------------------------------

MAX_ARTICLES: Final[int] = 10


# ---------------------------------------------------------
# OPENROUTER SETTINGS
# ---------------------------------------------------------

OPENROUTER_API_KEY: str = os.getenv(
    "OPENROUTER_API_KEY",
    ""
)

OPENROUTER_API_URL: Final[str] = (
    "https://openrouter.ai/api/v1/chat/completions"
)

OPENROUTER_MODEL: Final[str] = (
    "meta-llama/llama-3.1-8b-instruct"
)


# Optional OpenRouter headers
OPENROUTER_HTTP_REFERER: str = os.getenv(
    "OPENROUTER_HTTP_REFERER",
    "https://github.com/"
)

OPENROUTER_APP_NAME: str = os.getenv(
    "OPENROUTER_APP_NAME",
    "AI Finance News Agent"
)


# ---------------------------------------------------------
# AI SETTINGS
# ---------------------------------------------------------

AI_MAX_RETRIES: Final[int] = 3

AI_REQUEST_TIMEOUT: Final[int] = 45

AI_TEMPERATURE: Final[float] = 0.3

AI_MAX_TOKENS: Final[int] = 300