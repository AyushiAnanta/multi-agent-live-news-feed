"""
Open-Web Search Provider Abstraction Layer.

Supports pluggable search engines (Google News Open-Web Search, DuckDuckGo, Tavily)
to enable empirical comparison and zero-cost live web mining.
"""

import abc
import datetime
import logging
import os
import time
import urllib.parse
from typing import Any, Dict, List, Optional
import feedparser

logger = logging.getLogger(__name__)


class BaseSearchProvider(abc.ABC):
    """Abstract search provider interface for open-web news/article discovery."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abc.abstractmethod
    def search_news(
        self,
        query: str,
        max_results: int = 20,
        time_window_hours: Optional[float] = 24.0,
    ) -> List[Dict[str, Any]]:
        """
        Search open-web news sources for a query.

        Returns list of standardized article dicts:
        [
            {
                "title": str,
                "link": str,
                "summary": str,
                "published": ISO timestamp or None,
                "source": str (e.g. domain or outlet name),
                "id": str,
                "discovery_channel": "open_web"
            }
        ]
        """
        pass


class GoogleNewsSearchProvider(BaseSearchProvider):
    """
    Open-web news search provider leveraging Google News RSS index.
    Provides unauthenticated, rate-limit-free open-web news discovery across
    hundreds of thousands of global publications.
    """

    @property
    def name(self) -> str:
        return "google_news"

    def search_news(
        self,
        query: str,
        max_results: int = 20,
        time_window_hours: Optional[float] = 24.0,
    ) -> List[Dict[str, Any]]:
        articles: List[Dict[str, Any]] = []
        try:
            encoded_query = urllib.parse.quote(query)
            # ceid=US:en, gl=US, hl=en-US for broad english news
            feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            logger.info("Querying Google News RSS for: '%s'", query)

            feed = feedparser.parse(feed_url)
            entries = getattr(feed, "entries", [])
            logger.info("Google News RSS returned %d entries.", len(entries))

            now = datetime.datetime.now(datetime.timezone.utc)
            cutoff_time = (
                now - datetime.timedelta(hours=time_window_hours)
                if time_window_hours
                else None
            )

            seen_links = set()
            for entry in entries[: max_results * 2]:
                link = entry.get("link", "")
                if not link or link in seen_links:
                    continue
                seen_links.add(link)

                # Parse publication date
                pub_iso = None
                pub_dt = None
                if entry.get("published_parsed"):
                    try:
                        pub_dt = datetime.datetime.fromtimestamp(
                            time.mktime(entry.published_parsed), datetime.timezone.utc
                        )
                        pub_iso = pub_dt.isoformat()
                    except Exception:
                        pub_iso = now.isoformat()
                else:
                    pub_iso = now.isoformat()

                title = entry.get("title", "")
                source_meta = entry.get("source", {})
                source_title = source_meta.get("title") if isinstance(source_meta, dict) else ""
                
                # Split source from title if embedded e.g. "Headline - Source Name"
                if not source_title and " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_title = parts[1].strip()

                summary = entry.get("summary", "")

                articles.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": pub_iso,
                    "source": source_title or "Open Web",
                    "id": entry.get("id") or link,
                    "discovery_channel": "open_web",
                })

                if len(articles) >= max_results:
                    break

            # Parallel URL decoding to obtain genuine publisher links
            def _decode_single(art):
                raw_link = art["link"]
                if "news.google.com/rss/articles" in raw_link:
                    try:
                        from googlenewsdecoder import gnewsdecoder
                        decoded = gnewsdecoder(raw_link)
                        if decoded and decoded.get("success") and decoded.get("decoded_url"):
                            art["link"] = decoded["decoded_url"]
                            art["id"] = decoded["decoded_url"]
                    except Exception:
                        pass
                return art

            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as pool:
                articles = list(pool.map(_decode_single, articles))

            logger.info("Google News returned %d valid open-web articles.", len(articles))
        except Exception as exc:
            logger.error("Google News search failed: %s", exc)

        return articles


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Open-web news search provider using DuckDuckGo."""

    @property
    def name(self) -> str:
        return "duckduckgo"

    def search_news(
        self,
        query: str,
        max_results: int = 15,
        time_window_hours: Optional[float] = 24.0,
    ) -> List[Dict[str, Any]]:
        articles: List[Dict[str, Any]] = []
        try:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                from ddgs import DDGS  # type: ignore

            timelimit = "d"
            if time_window_hours and time_window_hours > 48:
                timelimit = "w" if time_window_hours <= 168 else "m"

            ddgs = DDGS()
            logger.info("Querying DuckDuckGo for: '%s'", query)
            raw_results = []
            
            # Try news first with graceful fallback to text
            try:
                raw_results = list(ddgs.news(query, timelimit=timelimit, max_results=max_results))
            except Exception as news_err:
                logger.warning("DDG news endpoint failed (%s); trying DDG text search...", news_err)
                try:
                    raw_results = list(ddgs.text(query, timelimit=timelimit, max_results=max_results))
                except Exception as text_err:
                    logger.error("DDG text search failed: %s", text_err)

            seen_urls = set()
            now = datetime.datetime.now(datetime.timezone.utc)

            for item in raw_results:
                link = item.get("url") or item.get("href") or item.get("link")
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                date_str = item.get("date")
                published_iso = now.isoformat()
                if date_str:
                    try:
                        pub_dt = datetime.datetime.fromisoformat(date_str)
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
                        published_iso = pub_dt.isoformat()
                    except Exception:
                        published_iso = now.isoformat()

                title = item.get("title", "").strip()
                summary = (item.get("body") or item.get("snippet") or "").strip()
                source = item.get("source") or item.get("publisher") or "Web Discovery"

                articles.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published_iso,
                    "source": source,
                    "id": link,
                    "discovery_channel": "open_web",
                })

            logger.info("DuckDuckGo returned %d valid open-web articles.", len(articles))
        except Exception as exc:
            logger.error("DuckDuckGo search error: %s", exc)

        return articles


class HybridOpenWebProvider(BaseSearchProvider):
    """
    Hybrid open-web discovery engine.
    Combines Google News open-web search with DuckDuckGo fallback for maximum
    heterogeneity, resilient uptime, and zero API cost.
    """

    def __init__(self):
        self.gnews = GoogleNewsSearchProvider()
        self.ddg = DuckDuckGoSearchProvider()

    @property
    def name(self) -> str:
        return "hybrid_open_web"

    def search_news(
        self,
        query: str,
        max_results: int = 20,
        time_window_hours: Optional[float] = 24.0,
    ) -> List[Dict[str, Any]]:
        # Primary: Google News RSS
        results = self.gnews.search_news(
            query=query,
            max_results=max_results,
            time_window_hours=time_window_hours,
        )

        # Supplement with DDG if fewer results
        if len(results) < max_results:
            supplemental = self.ddg.search_news(
                query=query,
                max_results=max_results - len(results),
                time_window_hours=time_window_hours,
            )
            existing_links = {a.get("link") for a in results}
            for art in supplemental:
                if art.get("link") not in existing_links:
                    results.append(art)

        return results[:max_results]


class TavilySearchProvider(BaseSearchProvider):
    """Tavily search provider optimized for LLM search (activated if API key is provided)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

    @property
    def name(self) -> str:
        return "tavily"

    def search_news(
        self,
        query: str,
        max_results: int = 15,
        time_window_hours: Optional[float] = 24.0,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found. Skipping Tavily provider.")
            return []

        articles: List[Dict[str, Any]] = []
        try:
            import requests

            days = max(1, int(round((time_window_hours or 24.0) / 24.0)))
            payload = {
                "api_key": self.api_key,
                "query": query,
                "topic": "news",
                "days": days,
                "max_results": max_results,
            }
            resp = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    link = item.get("url")
                    articles.append({
                        "title": item.get("title", ""),
                        "link": link,
                        "summary": item.get("content", ""),
                        "published": item.get("published_date") or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "source": item.get("source") or "Tavily News",
                        "id": link,
                        "discovery_channel": "open_web",
                    })
        except Exception as exc:
            logger.error("Tavily search error: %s", exc)

        return articles


def get_search_provider(preferred: Optional[str] = None) -> BaseSearchProvider:
    """Factory to instantiate configured search provider."""
    provider_type = (preferred or os.getenv("OPEN_WEB_SEARCH_PROVIDER", "hybrid")).lower().strip()

    if provider_type == "tavily" and os.getenv("TAVILY_API_KEY"):
        return TavilySearchProvider()
    elif provider_type == "google_news":
        return GoogleNewsSearchProvider()
    elif provider_type == "duckduckgo":
        return DuckDuckGoSearchProvider()

    # Default to Hybrid (Google News RSS + DuckDuckGo)
    return HybridOpenWebProvider()
