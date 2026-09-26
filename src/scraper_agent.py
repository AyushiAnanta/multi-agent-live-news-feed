"""
Generalized Web Content Extractor.

Supports arbitrary HTML extraction from previously unseen open-web domains
using Trafilatura (state-of-the-art news boilerplate removal) with BeautifulSoup
fallback, extracting clean article body, metadata, author, and publication dates.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import Any, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import requests

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScraperAgent:
    """Extracts clean article content and metadata from arbitrary web URLs."""

    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch raw HTML with standard headers and error handling."""
        try:
            logger.info("Fetching: %s", url)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200 and response.text:
                return response.text
            logger.warning("HTTP %d for URL: %s", response.status_code, url)
            return None
        except Exception as exc:
            logger.warning("Error fetching %s: %s", url, exc)
            return None

    def _extract_with_trafilatura(self, html: str, url: str = "") -> Optional[str]:
        """Extract clean body text using Trafilatura."""
        if not TRAFILATURA_AVAILABLE:
            return None
        try:
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_recall=True,
            )
            if text and len(text.strip()) > 100:
                return text.strip()
            return None
        except Exception as exc:
            logger.debug("Trafilatura extraction failed for %s: %s", url, exc)
            return None

    def _extract_with_bs4(self, html: str) -> str:
        """Fallback extraction using BeautifulSoup for legacy compatibility."""
        soup = BeautifulSoup(html, "html.parser")

        # Decompose non-content tags
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            element.decompose()

        # Prioritize <article> or <main> if present
        target = soup.find("article") or soup.find("main") or soup.body or soup
        text = target.get_text(separator=" ")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = "\n".join(lines)
        return cleaned[:10000]

    def extract_content(self, html: str, url: str = "") -> str:
        """
        Generalized extraction pipeline:
        1. Try Trafilatura (heuristic-based boilerplate elimination).
        2. Fall back to BeautifulSoup if Trafilatura is empty or unavailable.
        """
        extracted = self._extract_with_trafilatura(html, url=url)
        if extracted:
            return extracted[:12000]

        return self._extract_with_bs4(html)

    def extract_metadata(self, html: str, url: str = "") -> Dict[str, Any]:
        """Extract structured article metadata (title, date, author, sitename)."""
        meta = {
            "title": "",
            "author": "",
            "date": "",
            "sitename": "",
            "description": "",
        }
        if TRAFILATURA_AVAILABLE:
            try:
                metadata = trafilatura.extract_metadata(html, default_url=url)
                if metadata:
                    meta["title"] = metadata.title or ""
                    meta["author"] = metadata.author or ""
                    meta["date"] = metadata.date or ""
                    meta["sitename"] = metadata.sitename or ""
                    meta["description"] = metadata.description or ""
            except Exception as exc:
                logger.debug("Trafilatura metadata extraction failed: %s", exc)

        if not meta["title"]:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                meta["title"] = title_tag.get_text().strip()

        return meta

    def _scrape_single(self, url: str) -> Tuple[str, Optional[str]]:
        """Scrape a single URL. Returns (url, text) or (url, None)."""
        html = self._fetch_html(url)
        if not html:
            return url, None
        text = self.extract_content(html, url=url)
        return url, text if text else None

    def scrape_urls(self, urls: List[str]) -> Dict[str, str]:
        """
        Visits a list of URLs in parallel and scrapes their content.
        Returns a map of URL -> Cleaned Text.
        """
        results: Dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(self._scrape_single, url) for url in urls]
            for future in as_completed(futures):
                url, text = future.result()
                if text:
                    results[url] = text
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = ScraperAgent()
    test_url = "https://en.wikipedia.org/wiki/Web_mining"
    content = scraper.scrape_urls([test_url])
    print(f"Scraped {len(content)} URLs. Sample snippet:")
    for u, txt in content.items():
        print(f"[{u}]: {txt[:300]}...")
