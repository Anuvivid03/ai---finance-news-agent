"""
Fetch financial news from configured RSS feeds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from config import RSS_FEEDS, MAX_ARTICLES


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Article:
    """Represents a normalized financial news article."""

    title: str
    url: str
    summary: str
    source: str
    published_at: datetime


def clean_text(value: Optional[str]) -> str:
    """
    Clean unnecessary whitespace from text.

    Args:
        value: Raw text.

    Returns:
        Cleaned text.
    """

    if not value:
        return ""

    return " ".join(value.split()).strip()


def parse_date(entry: object) -> datetime:
    """
    Extract publication date from an RSS entry.

    Args:
        entry: RSS feed entry.

    Returns:
        Timezone-aware publication datetime.
    """

    published_parsed = getattr(
        entry,
        "published_parsed",
        None,
    )

    if published_parsed:
        try:
            return datetime(
                published_parsed.tm_year,
                published_parsed.tm_mon,
                published_parsed.tm_mday,
                published_parsed.tm_hour,
                published_parsed.tm_min,
                published_parsed.tm_sec,
                tzinfo=timezone.utc,
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            pass

    published = getattr(
        entry,
        "published",
        "",
    )

    updated = getattr(
        entry,
        "updated",
        "",
    )

    date_string = published or updated

    if date_string:
        try:
            parsed = parsedate_to_datetime(
                date_string
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            pass

    # If no date exists, use Unix epoch.
    return datetime(
        1970,
        1,
        1,
        tzinfo=timezone.utc,
    )


def fetch_feed(
    feed_name: str,
    feed_url: str,
) -> list[Article]:
    """
    Fetch articles from one RSS feed.

    Args:
        feed_name: Human-readable source name.
        feed_url: RSS feed URL.

    Returns:
        List of normalized articles.
    """

    try:
        logger.info(
            "Fetching: %s",
            feed_name,
        )

        feed = feedparser.parse(
            feed_url,
            agent=(
                "Mozilla/5.0 "
                "(compatible; "
                "AIFinanceNewsAgent/1.0)"
            ),
        )

        if getattr(feed, "bozo", False):
            logger.warning(
                "RSS parser warning for %s: %s",
                feed_name,
                getattr(
                    feed,
                    "bozo_exception",
                    "Unknown error",
                ),
            )

        entries = getattr(
            feed,
            "entries",
            [],
        )

        if not entries:
            logger.warning(
                "No articles found: %s",
                feed_name,
            )
            return []

        articles: list[Article] = []

        for entry in entries:
            title = clean_text(
                getattr(
                    entry,
                    "title",
                    "",
                )
            )

            url = clean_text(
                getattr(
                    entry,
                    "link",
                    "",
                )
            )

            summary = clean_text(
                getattr(
                    entry,
                    "summary",
                    "",
                )
                or getattr(
                    entry,
                    "description",
                    "",
                )
            )

            # Skip malformed entries.
            if not title or not url:
                logger.warning(
                    "Skipping malformed article from %s",
                    feed_name,
                )
                continue

            articles.append(
                Article(
                    title=title,
                    url=url,
                    summary=summary,
                    source=feed_name,
                    published_at=parse_date(entry),
                )
            )

        logger.info(
            "%s: %d articles fetched",
            feed_name,
            len(articles),
        )

        return articles

    except Exception as exc:
        logger.exception(
            "Failed to fetch %s: %s",
            feed_name,
            exc,
        )

        # Important:
        # One failed feed must NOT stop the whole pipeline.
        return []


def deduplicate_articles(
    articles: list[Article],
) -> list[Article]:
    """
    Remove duplicate articles based on URL.

    Args:
        articles: List of articles.

    Returns:
        Deduplicated articles.
    """

    seen_urls: set[str] = set()
    unique_articles: list[Article] = []

    for article in articles:
        normalized_url = (
            article.url
            .strip()
            .rstrip("/")
        )

        if not normalized_url:
            continue

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)
        unique_articles.append(article)

    return unique_articles


def fetch_latest_news() -> list[Article]:
    """
    Fetch, deduplicate, sort and limit financial news.

    Returns:
        Latest MAX_ARTICLES articles.
    """

    all_articles: list[Article] = []

    for feed_name, feed_url in RSS_FEEDS.items():
        articles = fetch_feed(
            feed_name,
            feed_url,
        )

        all_articles.extend(articles)

    if not all_articles:
        logger.warning(
            "No articles fetched from any RSS feed."
        )
        return []

    unique_articles = deduplicate_articles(
        all_articles
    )

    # Latest articles first.
    unique_articles.sort(
        key=lambda article: article.published_at,
        reverse=True,
    )

    latest_articles = unique_articles[
        :MAX_ARTICLES
    ]

    logger.info(
        "Fetched: %d | Unique: %d | Selected: %d",
        len(all_articles),
        len(unique_articles),
        len(latest_articles),
    )

    return latest_articles