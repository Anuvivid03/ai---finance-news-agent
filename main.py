"""
Main entry point for the AI Finance News Agent.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from database import (
    initialize_database,
    is_article_processed,
    mark_article_processed,
)
from fetch_news import Article, fetch_latest_news
from summarize import generate_daily_digest


OUTPUT_DIR = Path("output")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def save_digest(digest: list[dict]) -> Path:
    """Save the daily news digest as a JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_string = datetime.now().strftime("%Y-%m-%d")
    output_file = OUTPUT_DIR / f"news_digest_{date_string}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            digest,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_file


def filter_new_articles(
    articles: list[Article],
) -> list[Article]:
    """Return only articles that have not been processed before."""
    new_articles: list[Article] = []

    for article in articles:
        if is_article_processed(article.url):
            logger.info(
                "Skipping already processed article: %s",
                article.title,
            )
            continue

        new_articles.append(article)

    logger.info(
        "New articles: %d/%d",
        len(new_articles),
        len(articles),
    )

    return new_articles


def mark_successful_articles(
    digest: list[dict],
) -> None:
    """Mark successfully summarized articles as processed."""
    processed_at = datetime.now(timezone.utc).isoformat()

    for article in digest:
        mark_article_processed(
            url=article["url"],
            title=article["title"],
            processed_at=processed_at,
        )


def main() -> None:
    """Run the complete finance news pipeline."""
    logger.info("Starting AI Finance News Agent...")

    # Create the SQLite database/table if needed.
    initialize_database()

    # Fetch latest RSS articles.
    articles = fetch_latest_news()

    if not articles:
        logger.error("No news articles found.")
        return

    # Remove articles already processed previously.
    new_articles = filter_new_articles(articles)

    if not new_articles:
        logger.info("No new articles to process today.")
        return

    logger.info(
        "Generating AI captions for %d new articles...",
        len(new_articles),
    )

    # Generate AI captions.
    digest = generate_daily_digest(new_articles)

    if not digest:
        logger.error("No AI summaries were generated.")
        return

    # Mark only successfully summarized articles as processed.
    mark_successful_articles(digest)

    # Save the generated digest.
    output_file = save_digest(digest)

    logger.info(
        "SUCCESS: %d new articles saved to %s",
        len(digest),
        output_file,
    )


if __name__ == "__main__":
    main()
