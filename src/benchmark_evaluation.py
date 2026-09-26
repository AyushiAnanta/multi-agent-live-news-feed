"""
Empirical Benchmark & Comparative Evaluation Suite.
Phase II: Closed-List Ingestion vs. Open-Web Source Discovery.

Evaluates:
  1. Source Coverage (Total and Unique Domains)
  2. Unregistered Domain Discovery Rate
  3. Verified Article Yield (Credibility >= 80 and >= 50)
  4. Content Completeness & Extraction Success Rate
  5. Cluster Formation & Incremental Yield
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

# Ensure root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BenchmarkSuite")

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "category": "Artificial Intelligence",
        "query": "AI reasoning models and open source benchmarks",
    },
    {
        "id": "Q2",
        "category": "Geopolitics & Security",
        "query": "Red Sea shipping disruptions and maritime security",
    },
    {
        "id": "Q3",
        "category": "Space & Astrophysics",
        "query": "James Webb Space Telescope exoplanet atmospheric discoveries",
    },
    {
        "id": "Q4",
        "category": "Energy & Climate Policy",
        "query": "European Union carbon border adjustment mechanism enforcement",
    },
    {
        "id": "Q5",
        "category": "Semiconductors & Trade",
        "query": "Global semiconductor export controls and advanced chip manufacturing",
    },
    {
        "id": "Q6",
        "category": "Regional Infrastructure",
        "query": "India semiconductor manufacturing fab construction updates",
    },
]


def extract_base_domain(url: str) -> str:
    """Extract clean base domain from URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        parts = netloc.split(".")
        if len(parts) > 2 and parts[-2] in ("co", "com", "org", "net"):
            return ".".join(parts[-3:])
        elif len(parts) > 2:
            return ".".join(parts[-2:])
        return netloc
    except Exception:
        return "unknown"


def evaluate_run(result: Dict[str, Any], trusted_domains: set) -> Dict[str, Any]:
    """Calculate empirical metrics from a pipeline execution result."""
    all_articles = result.get("all_articles", [])
    trends = result.get("trends", [])

    total_articles = len(all_articles)
    domains = [extract_base_domain(a.get("link", "")) for a in all_articles if a.get("link")]
    unique_domains = sorted(list(set(d for d in domains if d and d != "unknown")))

    unregistered_domains = [d for d in unique_domains if d not in trusted_domains]

    verified_count = 0  # score >= 80
    likely_count = 0    # score >= 50
    total_score = 0.0

    for a in all_articles:
        score = a.get("verification_detail", {}).get("credibility_score", 0)
        total_score += score
        if score >= 80:
            verified_count += 1
        elif score >= 50:
            likely_count += 1

    mean_score = (total_score / total_articles) if total_articles > 0 else 0.0
    verified_yield_pct = (verified_count / total_articles * 100) if total_articles > 0 else 0.0
    effective_yield_pct = ((verified_count + likely_count) / total_articles * 100) if total_articles > 0 else 0.0

    return {
        "status": result.get("status", "unknown"),
        "total_articles": total_articles,
        "unique_domains_count": len(unique_domains),
        "unique_domains": unique_domains,
        "unregistered_domains_count": len(unregistered_domains),
        "unregistered_domains": unregistered_domains,
        "verified_articles": verified_count,
        "likely_articles": likely_count,
        "mean_credibility_score": round(mean_score, 2),
        "verified_yield_pct": round(verified_yield_pct, 1),
        "effective_yield_pct": round(effective_yield_pct, 1),
        "trends_synthesized": len(trends),
    }


def run_benchmark(max_queries: int = 6, write_report: bool = True):
    """Execute comparative benchmark across query set."""
    orchestrator = Orchestrator()
    trusted_domains = orchestrator.verifier.trusted_domains

    selected_queries = BENCHMARK_QUERIES[:max_queries]
    benchmark_data = []

    print("=" * 80)
    print("STARTING EMPIRICAL BENCHMARK: CLOSED-LIST VS. OPEN-WEB DISCOVERY")
    print(f"Total Queries: {len(selected_queries)} | Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    for item in selected_queries:
        qid = item["id"]
        category = item["category"]
        query = item["query"]

        print(f"\n[{qid}] Category: {category} | Query: '{query}'")

        # ----------------------------------------------------
        # 1. Closed-List RSS Only (Baseline)
        # ----------------------------------------------------
        print(f"  -> Running Baseline (Closed-List RSS Only)...")
        start_t0 = time.time()
        try:
            res_closed = orchestrator.run_search_pipeline(
                query,
                algorithm="hdbscan",
                open_web_discovery=False,
                write_output=False,
            )
        except Exception as exc:
            logger.error("Closed-list run failed: %s", exc)
            res_closed = {"status": "error", "all_articles": [], "trends": []}
        elapsed_closed = round(time.time() - start_t0, 2)
        metrics_closed = evaluate_run(res_closed, trusted_domains)
        metrics_closed["latency_sec"] = elapsed_closed

        # ----------------------------------------------------
        # 2. Extended Open-Web Discovery (Proposed Phase II)
        # ----------------------------------------------------
        print(f"  -> Running Extended Pipeline (RSS + Open-Web Discovery)...")
        start_t1 = time.time()
        try:
            res_open = orchestrator.run_search_pipeline(
                query,
                algorithm="hdbscan",
                open_web_discovery=True,
                write_output=False,
            )
        except Exception as exc:
            logger.error("Open-web run failed: %s", exc)
            res_open = {"status": "error", "all_articles": [], "trends": []}
        elapsed_open = round(time.time() - start_t1, 2)
        metrics_open = evaluate_run(res_open, trusted_domains)
        metrics_open["latency_sec"] = elapsed_open

        # Record comparative data
        record = {
            "query_id": qid,
            "category": category,
            "query": query,
            "closed_list": metrics_closed,
            "open_web": metrics_open,
            "domain_coverage_gain": metrics_open["unique_domains_count"] - metrics_closed["unique_domains_count"],
            "article_yield_gain": metrics_open["total_articles"] - metrics_closed["total_articles"],
        }
        benchmark_data.append(record)

        print(
            f"  [Summary {qid}] Closed Domains: {metrics_closed['unique_domains_count']} | "
            f"Open Domains: {metrics_open['unique_domains_count']} (+{record['domain_coverage_gain']}) | "
            f"Articles: {metrics_closed['total_articles']} -> {metrics_open['total_articles']} | "
            f"New Unregistered Domains: {metrics_open['unregistered_domains_count']}"
        )

    # ----------------------------------------------------
    # Generate Formatted Tables & Output
    # ----------------------------------------------------
    report = generate_report(benchmark_data)

    if write_report:
        report_path = "benchmark_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "benchmark_data": benchmark_data,
                "summary": report["summary"],
            }, f, indent=2)

        md_path = "BENCHMARK_RESULTS.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report["markdown"])

        print(f"\n[Saved benchmark report to {report_path} and {md_path}]")

    print("\n" + report["markdown"])
    return benchmark_data


def generate_report(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate Markdown and LaTeX tables summarizing benchmark results."""
    total_closed_arts = sum(d["closed_list"]["total_articles"] for d in data)
    total_open_arts = sum(d["open_web"]["total_articles"] for d in data)

    total_closed_domains = sum(d["closed_list"]["unique_domains_count"] for d in data)
    total_open_domains = sum(d["open_web"]["unique_domains_count"] for d in data)

    total_unregistered = sum(d["open_web"]["unregistered_domains_count"] for d in data)
    total_open_verified = sum(d["open_web"]["verified_articles"] for d in data)
    total_closed_verified = sum(d["closed_list"]["verified_articles"] for d in data)

    avg_score_closed = (
        sum(d["closed_list"]["mean_credibility_score"] for d in data) / len(data)
        if data else 0.0
    )
    avg_score_open = (
        sum(d["open_web"]["mean_credibility_score"] for d in data) / len(data)
        if data else 0.0
    )

    domain_expansion_pct = (
        ((total_open_domains - total_closed_domains) / total_closed_domains * 100)
        if total_closed_domains > 0 else 100.0
    )

    summary = {
        "total_queries": len(data),
        "total_articles_closed": total_closed_arts,
        "total_articles_open": total_open_arts,
        "total_domains_closed": total_closed_domains,
        "total_domains_open": total_open_domains,
        "domain_expansion_pct": round(domain_expansion_pct, 1),
        "total_unregistered_domains_discovered": total_unregistered,
        "total_verified_closed": total_closed_verified,
        "total_verified_open": total_open_verified,
        "mean_score_closed": round(avg_score_closed, 2),
        "mean_score_open": round(avg_score_open, 2),
    }

    # Markdown Table
    md = []
    md.append("# Phase II Empirical Evaluation: Closed-List vs. Open-Web Discovery\n")
    md.append(f"**Evaluation Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append(f"**Search Engine:** DuckDuckGo News (`ddgs`) | **Extractor:** Trafilatura  \n")
    md.append("### Comparative Performance Table\n")
    md.append("| Query ID | Topic / Category | Closed Articles | Open Articles | Closed Domains | Open Domains | Discovered Unregistered Domains | Verified Yield (Open) | Latency (Closed/Open) |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for d in data:
        qid = d["query_id"]
        cat = d["category"]
        c_art = d["closed_list"]["total_articles"]
        o_art = d["open_web"]["total_articles"]
        c_dom = d["closed_list"]["unique_domains_count"]
        o_dom = d["open_web"]["unique_domains_count"]
        unreg = d["open_web"]["unregistered_domains_count"]
        v_yield = f"{d['open_web']['verified_articles']} ({d['open_web']['verified_yield_pct']}%)"
        lat = f"{d['closed_list']['latency_sec']}s / {d['open_web']['latency_sec']}s"

        md.append(f"| **{qid}** | {cat} | {c_art} | {o_art} | {c_dom} | {o_dom} | **+{unreg}** | {v_yield} | {lat} |")

    md.append("\n### Aggregate Metrics Summary\n")
    md.append(f"- **Total Articles Retrieved:** Closed-List = `{total_closed_arts}`, Extended Open-Web = `{total_open_arts}` (`+{total_open_arts - total_closed_arts}` articles)")
    md.append(f"- **Domain Coverage Expansion:** `{total_closed_domains}` $\\rightarrow$ `{total_open_domains}` unique domains (**+{domain_expansion_pct}% expansion**)")
    md.append(f"- **Unregistered Open-Web Domains Mined:** `{total_unregistered}` distinct domains discovered outside the seed whitelist")
    md.append(f"- **Total Verified Articles (Score $\\ge$ 80):** Closed-List = `{total_closed_verified}`, Extended Open-Web = `{total_open_verified}`")
    md.append(f"- **Mean Credibility Score:** Closed-List = `{round(avg_score_closed, 1)}/100`, Extended Open-Web = `{round(avg_score_open, 1)}/100`")

    return {
        "summary": summary,
        "markdown": "\n".join(md),
    }


if __name__ == "__main__":
    run_benchmark(max_queries=6)
