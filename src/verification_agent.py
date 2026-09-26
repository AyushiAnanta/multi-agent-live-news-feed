import json
import os
import logging
from urllib.parse import urlparse
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SENTENCE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Module-level cache: load the model once, reuse across all instances
_SENTENCE_MODEL = None


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_sentence_model():
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME") or None
        local_only = _env_flag("SENTENCE_TRANSFORMERS_LOCAL_ONLY") or _env_flag("HF_HUB_OFFLINE")
        logger.info(
            "Loading SentenceTransformer model %s (local_only=%s, cache_folder=%s)",
            SENTENCE_MODEL_NAME,
            local_only,
            cache_folder or "default",
        )
        _SENTENCE_MODEL = SentenceTransformer(
            SENTENCE_MODEL_NAME,
            cache_folder=cache_folder,
            local_files_only=local_only,
        )
    return _SENTENCE_MODEL


class VerificationAgent:

    def __init__(self, feeds_path="feeds_default.json"):
        # Lightweight semantic model for cross-source corroboration (cached)
        self.model = _get_sentence_model()

        # Load trusted domains from feeds_default.json
        self.trusted_domains = self._load_trusted_domains(feeds_path)


    # -----------------------------------------
    # Load trusted domains from feeds_default.json
    # -----------------------------------------
    def _load_trusted_domains(self, feeds_path):
        """
        Extract base domains from feeds_default.json URLs.
        These are considered editorially trusted sources.
        """
        trusted = set()
        try:
            with open(feeds_path, "r") as f:
                feeds = json.load(f)
            for url in feeds:
                domain = self._extract_domain(url)
                if domain:
                    trusted.add(domain)
        except Exception as e:
            logger.warning(f"Could not load feeds_default.json for trusted domains: {e}")
        
        logger.info(f"Loaded {len(trusted)} trusted domains: {trusted}")
        return trusted


    # -----------------------------------------
    # Extract domain from a URL
    # -----------------------------------------
    def _extract_domain(self, url):
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            # Strip subdomains for feed URLs like feeds.bbci.co.uk -> bbci.co.uk
            # But keep meaningful ones like rss.nytimes.com -> nytimes.com
            parts = domain.split(".")
            if len(parts) > 2:
                # Keep last two parts for standard TLDs (.com, .org)
                # Keep last three for country TLDs (.co.uk)
                if parts[-2] in ("co", "com", "org", "net"):
                    domain = ".".join(parts[-3:])
                else:
                    domain = ".".join(parts[-2:])
            return domain
        except Exception:
            return ""


    # -----------------------------------------
    # Check if domain is in trusted sources
    # -----------------------------------------
    def _is_trusted_source(self, domain):
        return domain in self.trusted_domains


    # -----------------------------------------
    # Cross-Source Corroboration
    # Returns count of unique corroborating domains
    # -----------------------------------------
    def _count_corroborating_domains(self, article_index, embeddings, articles):
        """
        Find articles semantically similar to the given one,
        then count how many UNIQUE domains they come from.
        5 articles from nytimes.com = 1 corroborating domain, not 5.
        """
        emb1 = embeddings[article_index]
        source_domain = self._extract_domain(articles[article_index].get("link", ""))

        corroborating_domains = set()

        for i, emb2 in enumerate(embeddings):
            if i == article_index:
                continue

            similarity = util.cos_sim(emb1, emb2).item()

            if similarity >= 0.58:
                other_domain = self._extract_domain(articles[i].get("link", ""))
                # Only count if it's a DIFFERENT domain
                if other_domain and other_domain != source_domain:
                    corroborating_domains.add(other_domain)

        return corroborating_domains


    # -----------------------------------------
    # Content Completeness Score
    # -----------------------------------------
    def _content_completeness_score(self, article):
        """
        Check if the article has meaningful metadata.
        Up to 15 points.
        """
        score = 0

        # Has a real headline (not empty, not too short)
        title = article.get("title", "")
        if len(title) > 20:
            score += 5

        # Has a non-empty summary
        summary = article.get("summary", "")
        if len(summary.strip()) > 0:
            score += 5

        # Has a published date
        if article.get("published"):
            score += 5

        return score


    # -----------------------------------------
    # Recency Score
    # -----------------------------------------
    def _recency_score(self, article):
        """
        How recent is the article? Up to 10 points.
        Articles within 6 hours get full points, decaying to 0 at 48h+.
        """
        published = article.get("published", "")
        if not published:
            return 0

        try:
            pub_dt = datetime.fromisoformat(published)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age_hours = (now - pub_dt).total_seconds() / 3600

            if age_hours <= 6:
                return 10
            elif age_hours <= 12:
                return 7
            elif age_hours <= 24:
                return 4
            elif age_hours <= 48:
                return 2
            else:
                return 0
        except Exception:
            return 0


    # -----------------------------------------
    # -----------------------------------------
    # Domain Reputation Score (Recalibrated for Open Web)
    # -----------------------------------------
    def _domain_reputation_score(self, domain, link=""):
        """
        Evaluate domain credibility without penalizing unregistered open-web sources.
        Pre-registered trusted sources get 30 pts.
        Unregistered open-web domains get evaluated on structural legitimacy (up to 20 pts).
        """
        if not domain:
            return 0

        # Whitelisted trusted source
        if self._is_trusted_source(domain):
            return 30

        # High-trust TLDs
        if domain.endswith((".gov", ".edu", ".ac.uk", ".gov.uk", ".int")):
            return 25

        # Check for suspicious patterns (e.g. raw IP addresses or obvious temp domains)
        import re
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
            return 0

        # Reputable established standard news/web TLDs with secure link
        valid_tlds = (
            ".com", ".org", ".net", ".news", ".co", ".in", ".co.uk", ".io",
            ".ai", ".de", ".fr", ".jp", ".ca", ".au", ".eu", ".tech"
        )
        is_https = link.startswith("https://") if link else True
        if any(domain.endswith(tld) for tld in valid_tlds):
            return 20 if is_https else 14

        return 10

    # -----------------------------------------
    # Main Verification Logic (Recalibrated for Open-Web MAS)
    # -----------------------------------------
    def verify(self, articles):
        """
        Score each article on a recalibrated 0-100 credibility scale.

        Scoring breakdown (recalibrated for open-web discovery):
          - Domain Reputation:         0 - 30 pts  (trusted whitelist: 30, legitimate open-web: 15-25)
          - Cross-Source Corroboration: 0 - 45 pts  (unique independent reporting domains)
          - Content Completeness:      0 - 15 pts  (headline, summary, date present)
          - Recency:                   0 - 10 pts  (freshness decay curve)

        Thresholds:
          80-100  -> verified
          50-79   -> likely
          20-49   -> uncertain
          0-19    -> unverified
        """
        if not articles:
            return []

        texts_to_encode = [
            f"{a.get('title', '')} {a.get('summary', '')[:120]}".strip()
            for a in articles
        ]

        # Encode all article texts once
        embeddings = self.model.encode(
            texts_to_encode,
            convert_to_tensor=True,
            show_progress_bar=False
        )

        verified_articles = []

        for idx, article in enumerate(articles):
            domain = self._extract_domain(article.get("link", ""))
            link = article.get("link", "")

            # --- 1. Domain Reputation (0-30 pts) ---
            source_score = self._domain_reputation_score(domain, link)

            # --- 2. Cross-Source Corroboration (0-45 pts) ---
            corroborating = self._count_corroborating_domains(idx, embeddings, articles)
            num_corroborating = len(corroborating)

            # Boosted corroboration curve for open-web discovery
            if num_corroborating >= 3:
                corroboration_score = 45
            elif num_corroborating == 2:
                corroboration_score = 34
            elif num_corroborating == 1:
                corroboration_score = 22
            else:
                corroboration_score = 0

            # --- 3. Content Completeness (0-15 pts) ---
            completeness_score = self._content_completeness_score(article)

            # --- 4. Recency (0-10 pts) ---
            recency = self._recency_score(article)

            # --- Final Score (0 - 100) ---
            credibility_score = min(100, source_score + corroboration_score + completeness_score + recency)

            # Determine status
            if credibility_score >= 80:
                status = "verified"
            elif credibility_score >= 50:
                status = "likely"
            elif credibility_score >= 20:
                status = "uncertain"
            else:
                status = "unverified"

            article["verification_status"] = status
            article["verification_detail"] = {
                "domain": domain,
                "is_trusted_source": self._is_trusted_source(domain),
                "corroborating_domains": list(corroborating),
                "source_score": source_score,
                "corroboration_score": corroboration_score,
                "completeness_score": completeness_score,
                "recency_score": recency,
                "credibility_score": credibility_score,
            }

            verified_articles.append(article)

        return verified_articles
