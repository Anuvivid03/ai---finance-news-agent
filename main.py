"""
Main entry point for the AI Finance News Agent.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from fetch_news import fetch_latest_news
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


def main() -> None:
    """Run the complete finance news pipeline."""
    logger.info("Starting AI Finance News Agent...")

    articles = fetch_latest_news()

    if not articles:
        logger.error("No news articles found.")
        return

    logger.info("Generating AI captions for %d articles...", len(articles))

    digest = generate_daily_digest(articles)

    if not digest:
        logger.error("No AI summaries were generated.")
        return

    output_file = save_digest(digest)

    logger.info(
        "SUCCESS: %d articles saved to %s",
        len(digest),
        output_file,
    )


if __name__ == "__main__":
    main()