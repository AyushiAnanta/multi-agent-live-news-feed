# Project Completion Report: Phase II Extension
## Exploring Multi-Agent System Design for Efficient Web Data Mining
### Subtitle: From Closed-List Aggregation to Open-Web Source Discovery
**Prepared for:** Ayushi Ananta  
**Date of Completion:** September 26, 2026  
**System Architecture:** Multi-Agent System (MAS) atop MERN + FastAPI Worker  

---

## 1. Executive Summary & Objective

In Phase I, the system was implemented as a 6-stage news aggregation pipeline (Poll $\to$ Verify $\to$ Cluster $\to$ Scrape $\to$ Synthesize). However, its ingestion was constrained to a fixed, pre-registered whitelist of 11 RSS feeds, creating a fundamental gap between the project's stated scope (**"Web Data Mining"**) and its actual implementation (**"Closed-List RSS Aggregation"**).

**Phase II Objective:**
To break out of the closed-list boundary by extending the multi-agent system's ingestion layer toward **genuine open-web source discovery** — enabling the system to autonomously discover, extract from, and credibility-score heterogeneous web sources it was not pre-configured to monitor, and to empirically benchmark this capability against the baseline.

All five core methodology deliverables have been engineered, integrated, and validated.

---

## 2. Summary of Implemented & Validated Components

| Deliverable | File(s) Modified / Created | Operational Status | Technical Implementation Details |
| :--- | :--- | :---: | :--- |
| **1. Pluggable Search Provider Layer** | [`src/search_providers.py`](src/search_providers.py) | **COMPLETE & TESTED** | Abstract base class `BaseSearchProvider` with implementations for `GoogleNewsSearchProvider`, `DuckDuckGoSearchProvider`, `HybridOpenWebProvider`, and `TavilySearchProvider`. Includes parallel URL decoding (`googlenewsdecoder` + `ThreadPoolExecutor`) to resolve direct publisher URLs. |
| **2. Dual-Channel Discovery Agent** | [`src/search_agent.py`](src/search_agent.py) | **COMPLETE & TESTED** | Extends query parsing into an autonomous Scout Agent that matches pre-registered RSS feeds while concurrently dispatching live open-web discovery queries across global publishers. |
| **3. Generalized Content Extractor** | [`src/scraper_agent.py`](src/scraper_agent.py) | **COMPLETE & TESTED** | Replaced naive HTML parsing with `trafilatura` for state-of-the-art news boilerplate, navigation, and sidebar elimination, with BeautifulSoup fallback for structured metadata recovery (title, author, date). |
| **4. Recalibrated Credibility Model** | [`src/verification_agent.py`](src/verification_agent.py) | **COMPLETE & TESTED** | Eliminated the 35-point penalty for unregistered domains. Implemented structural domain legitimacy (0–30 pts), boosted cross-source corroboration using SentenceTransformer `all-MiniLM-L6-v2` embeddings (0–45 pts), content completeness (0–15 pts), and recency decay (0–10 pts). |
| **5. Pipeline Ingestion & Orchestration** | [`src/orchestrator.py`](src/orchestrator.py)<br>[`src/api.py`](src/api.py)<br>[`backend/src/server.js`](backend/src/server.js) | **COMPLETE & TESTED** | Merged candidate streams from RSS and Open-Web, tagged discovery channels (`rss` vs `open_web`), deduplicated by canonical link, and forwarded `open_web_discovery` parameter across FastAPI and Express. |
| **6. Empirical Evaluation Suite** | [`src/benchmark_evaluation.py`](src/benchmark_evaluation.py) | **COMPLETE & TESTED** | Automated benchmark harness evaluating 6 diverse query categories across Closed-List vs. Open-Web discovery. Generates `benchmark_report.json` and Markdown tables. |

---

## 3. Empirical Benchmark Results (Closed-List vs. Open-Web)

The empirical evaluation was conducted across 6 representative, non-trivial topic categories to evaluate the system's ability to discover specialized, heterogeneous content:

* **Q1 (Artificial Intelligence):** *"AI reasoning models and open source benchmarks"*
* **Q2 (Geopolitics & Security):** *"Red Sea shipping disruptions and maritime security"*
* **Q3 (Space & Astrophysics):** *"James Webb Space Telescope exoplanet atmospheric discoveries"*
* **Q4 (Energy & Climate Policy):** *"European Union carbon border adjustment mechanism enforcement"*
* **Q5 (Semiconductors & Trade):** *"Global semiconductor export controls and advanced chip manufacturing"*
* **Q6 (Regional Infrastructure):** *"India semiconductor manufacturing fab construction updates"*

### Comparative Results Table

| Query ID | Topic / Category | Baseline (Closed RSS) Articles | Open-Web Discovered Articles | Closed Unique Domains | Open-Web Unique Domains | Net Unregistered Domains Discovered | Verified Yield (Score $\ge$ 80) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1** | Artificial Intelligence | 0 | **20** | 0 | **16** | **+16** | 0 (0.0%) |
| **Q2** | Geopolitics & Security | 0 | **20** | 0 | **18** | **+18** | **13 (65.0%)** |
| **Q3** | Space & Astrophysics | 0 | **20** | 0 | **12** | **+12** | **8 (40.0%)** |
| **Q4** | Energy & Climate Policy | 1 | **21** | 1 | **20** | **+19** | **10 (47.6%)** |
| **Q5** | Semiconductors & Trade | 0 | **20** | 0 | **19** | **+19** | **5 (25.0%)** |
| **Q6** | Regional Infrastructure | 1 | **21** | 1 | **15** | **+15** | **10 (47.6%)** |

### Aggregate Metrics Comparison

| Metric | Closed-List Baseline | Extended Open-Web MAS | Absolute / Relative Improvement |
| :--- | :---: | :---: | :---: |
| **Total Ingested Articles** | 2 | **122** | **+120 articles (+6,000%)** |
| **Unique Domain Coverage** | 2 | **100** | **+98 domains (+4,900%)** |
| **Unregistered Domains Discovered** | 0 | **99** | **99 distinct global publishers** |
| **Verified Articles (Score $\ge$ 80)** | 0 | **46** | **+46 verified high-credibility articles** |
| **Mean Credibility Score** | 15.2 / 100 | **59.6 / 100** | **+44.4 points (+292%)** |
| **Average Query Latency** | 1.85s | **8.98s** | Sub-10s for full multi-agent discovery & verification |

---

## 4. Academic Analysis & Methodological Insights

### 1. The Closed-List Starvation Problem
For queries Q1, Q2, Q3, and Q5, the closed-list RSS baseline returned **0 articles**. Pre-registered general feeds (e.g. NYT Tech, BBC World) cycle rapidly and rarely cover niche technical or fast-evolving topics at the exact moment of querying. Closed-list systems suffer from severe content starvation outside mainstream headlines.

### 2. Heterogeneous Source Diversity
The open-web discovery layer mined articles from **99 distinct unregistered domains**, including specialized academic and technical outlets (`nature.com`, `tether.io`, `freshplaza.com`, `moderndiplomacy.eu`, `telecomlead.com`, `gminsights.com`, `politicstoday.org`).

### 3. Validation of Recalibrated Credibility
Under the old model, all 99 unregistered domains would have received a source score of 0/35, capping their maximum possible score at 65 and rendering zero "verified" articles. Under the recalibrated model, articles with strong cross-source corroboration and complete metadata achieved credibility scores above 80 (yielding **46 verified articles**).

---

## 5. How to Run and Reproduce

### Run the Benchmark Suite:
```bash
python -c "from src.benchmark_evaluation import run_benchmark; run_benchmark(max_queries=6)"
```
This generates `benchmark_report.json` and updates `BENCHMARK_RESULTS.md`.

### Run Open-Web Discovery via Python API:
```python
from src.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.run_search_pipeline(
    "AI reasoning models and open source benchmarks",
    algorithm="hdbscan",
    open_web_discovery=True
)
print(f"Total articles found: {len(result['all_articles'])}")
```

### Run via FastAPI Worker:
```bash
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```
POST to `/jobs/search` with payload:
```json
{
  "query": "Quantum computing hardware advancements",
  "algorithm": "hdbscan",
  "open_web_discovery": true
}
```
