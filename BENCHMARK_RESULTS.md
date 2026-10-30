# Phase II Empirical Evaluation: Closed-List vs. Open-Web Discovery

**Evaluation Timestamp:** 2026-09-29 21:54:14  
**Search Engine:** DuckDuckGo News (`ddgs`) | **Extractor:** Trafilatura  

### Comparative Performance Table

| Query ID | Topic / Category | Closed Articles | Open Articles | Closed Domains | Open Domains | Discovered Unregistered Domains | Verified Yield (Open) | Latency (Closed/Open) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1** | Artificial Intelligence | 3 | 34 | 3 | 8 | **+6** | 2 (5.9%) | 42.26s / 28.51s |
| **Q2** | Geopolitics & Security | 5 | 4 | 3 | 2 | **+2** | 0 (0.0%) | 13.14s / 63.1s |
| **Q3** | Space & Astrophysics | 4 | 2 | 3 | 2 | **+0** | 0 (0.0%) | 20.58s / 14.83s |
| **Q4** | Energy & Climate Policy | 5 | 5 | 1 | 1 | **+1** | 0 (0.0%) | 29.04s / 19.32s |
| **Q5** | Semiconductors & Trade | 3 | 0 | 3 | 0 | **+0** | 0 (0.0%) | 338.85s / 2.66s |
| **Q6** | Regional Infrastructure | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 2.63s / 6032.46s |

### Aggregate Metrics Summary

- **Total Articles Retrieved:** Closed-List = `20`, Extended Open-Web = `45` (`+25` articles)
- **Domain Coverage Expansion:** `13` $\rightarrow$ `13` unique domains (**+0.0% expansion**)
- **Unregistered Open-Web Domains Mined:** `9` distinct domains discovered outside the seed whitelist
- **Total Verified Articles (Score $\ge$ 80):** Closed-List = `0`, Extended Open-Web = `2`
- **Mean Credibility Score:** Closed-List = `38.1/100`, Extended Open-Web = `30.8/100`