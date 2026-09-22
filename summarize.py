"""
AI-powered summarization for financial news.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from config import (
    AI_MAX_RETRIES,
    AI_MAX_TOKENS,
    AI_REQUEST_TIMEOUT,
    AI_TEMPERATURE,
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_APP_NAME,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
)
from fetch_news import Article

logger = logging.getLogger(__name__)


def build_prompt(article: Article) -> str:
    """Build a high-quality Instagram finance-news prompt."""
    return f"""
You are an Indian financial news editor creating Instagram captions.

ARTICLE TITLE:
{article.title}

ARTICLE SUMMARY:
{article.summary}

SOURCE:
{article.source}

Create a short, factual Instagram finance-news caption.

Return ONLY valid JSON in exactly this format:

{{
  "headline": "emoji + short headline",
  "summary": "2-3 short lines",
  "hashtags": ["#Finance", "#StockMarket", "#News"]
}}

STRICT WRITING RULES:

1. Write in NATURAL INDIAN HINGLISH.
2. Use ROMAN ENGLISH letters only. Do NOT use Hindi Devanagari script.
3. Mix simple Hindi and English naturally.
4. Keep financial terms in English where appropriate:
   IPO, Nifty, Sensex, RBI, SEBI, stocks, shares, crude oil, rupee, market, investors, etc.
5. Do NOT translate financial terms into awkward Hindi.
6. Headline must be short, clear and attention-grabbing.
7. Headline should normally be 5-10 words.
8. Summary must contain 2-3 short, easy-to-read lines.
9. Explain WHAT happened, using only information available in the article.
10. Do NOT add information that is not present in the article.
11. Do NOT give investment advice.
12. Do NOT tell people to BUY, SELL or HOLD.
13. Do NOT make predictions about prices or markets.
14. Do NOT use phrases like "investors should buy", "big opportunity", or "guaranteed profit".
15. Avoid clickbait and exaggerated language.
16. Use 3-5 relevant hashtags.
17. Always include #Finance and #StockMarket.
18. Add 1-3 topic-specific hashtags when relevant.
19. Keep the tone professional but social-media friendly.
20. Do not mention that you are an AI.

QUALITY EXAMPLES:

Bad:
"Indonesia Banayat Naya Body"

Good:
"🇮🇩 Indonesia banayega naya land reform body"

Bad:
"📈 Rupee ke nirantar badlav kya hain?"

Good:
"💱 Rupee par oil prices ka pressure"

Bad:
"Nvidia shares now sell for half the price..."

Good Hinglish:
"💻 Nvidia shares mein badi girawat"

Remember:
- Natural Hinglish
- Roman script only
- Factual
- Short
- Instagram-friendly

Return ONLY JSON. No markdown. No explanation.
""".strip()


def parse_ai_response(content: str) -> dict[str, Any]:
    """Parse and validate the model's JSON response."""
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1).strip()

    data = json.loads(content)

    headline = str(data.get("headline", "")).strip()
    summary = str(data.get("summary", "")).strip()
    hashtags = data.get("hashtags", [])

    if not headline or not summary:
        raise ValueError("AI response is missing headline or summary.")

    if not isinstance(hashtags, list):
        hashtags = []

    hashtags = [
        str(tag).strip()
        for tag in hashtags
        if str(tag).strip()
    ][:5]

    if "#Finance" not in hashtags:
        hashtags.insert(0, "#Finance")

    if "#StockMarket" not in hashtags:
        hashtags.insert(1, "#StockMarket")

    hashtags = hashtags[:5]

    return {
        "headline": headline,
        "summary": summary,
        "hashtags": hashtags,
    }


def summarize_article(article: Article) -> dict[str, Any] | None:
    """Generate an AI summary for one article."""
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is missing.")
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_NAME,
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": AI_TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a factual Indian financial news editor. "
                    "Write natural Roman-script Hinglish captions "
                    "for Instagram. Never invent facts."
                ),
            },
            {
                "role": "user",
                "content": build_prompt(article),
            },
        ],
    }

    for attempt in range(1, AI_MAX_RETRIES + 1):
        try:
            logger.info(
                "AI summarization attempt %d/%d: %s",
                attempt,
                AI_MAX_RETRIES,
                article.title,
            )

            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=AI_REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "5")

                try:
                    wait_seconds = int(retry_after)
                except ValueError:
                    wait_seconds = 5

                logger.warning(
                    "Rate limited. Waiting %d seconds.",
                    wait_seconds,
                )

                time.sleep(wait_seconds)
                continue

            if response.status_code >= 500:
                logger.warning(
                    "OpenRouter server error: HTTP %d",
                    response.status_code,
                )

                if attempt < AI_MAX_RETRIES:
                    time.sleep(2 ** (attempt - 1))
                    continue

            response.raise_for_status()

            response_data = response.json()

            content = response_data["choices"][0]["message"]["content"]

            ai_result = parse_ai_response(content)

            hashtags = " ".join(ai_result["hashtags"])

            caption = (
                f"{ai_result['headline']}\n\n"
                f"{ai_result['summary']}\n\n"
                f"{hashtags}\n\n"
                f"Source: {article.source}"
            )

            return {
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at.isoformat(),
                "headline": ai_result["headline"],
                "summary": ai_result["summary"],
                "hashtags": ai_result["hashtags"],
                "caption": caption,
            }

        except (
            requests.RequestException,
            KeyError,
            IndexError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning(
                "AI request failed on attempt %d: %s",
                attempt,
                exc,
            )

            if attempt < AI_MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))

        except Exception as exc:
            logger.exception(
                "Unexpected AI error: %s",
                exc,
            )
            break

    logger.error("Failed to summarize article: %s", article.title)
    return None


def generate_daily_digest(
    articles: list[Article],
) -> list[dict[str, Any]]:
    """Generate AI captions for all fetched articles."""
    results: list[dict[str, Any]] = []

    for article in articles:
        result = summarize_article(article)

        if result is not None:
            results.append(result)

    logger.info(
        "AI digest completed: %d/%d articles summarized.",
        len(results),
        len(articles),
    )

    return results
