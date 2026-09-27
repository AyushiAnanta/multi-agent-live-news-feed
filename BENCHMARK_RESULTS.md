# Phase II Empirical Evaluation: Closed-List vs. Open-Web Discovery

**Evaluation Timestamp:** 2026-09-27 22:57:42  
**Search Engine:** DuckDuckGo News (`ddgs`) | **Extractor:** Trafilatura  

### Comparative Performance Table

| Query ID | Topic / Category | Closed Articles | Open Articles | Closed Domains | Open Domains | Discovered Unregistered Domains | Verified Yield (Open) | Latency (Closed/Open) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1** | Artificial Intelligence | 2 | 3 | 1 | 2 | **+1** | 0 (0.0%) | 31.36s / 28.31s |
| **Q2** | Geopolitics & Security | 1 | 1 | 1 | 1 | **+1** | 0 (0.0%) | 13.94s / 14.65s |
| **Q3** | Space & Astrophysics | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 5.09s / 5.36s |
| **Q4** | Energy & Climate Policy | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 4.48s / 5.08s |
| **Q5** | Semiconductors & Trade | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 3.88s / 6.8s |
| **Q6** | Regional Infrastructure | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 9.82s / 8.92s |

### Aggregate Metrics Summary

- **Total Articles Retrieved:** Closed-List = `3`, Extended Open-Web = `4` (`+1` articles)
- **Domain Coverage Expansion:** `2` $\rightarrow$ `3` unique domains (**+50.0% expansion**)
- **Unregistered Open-Web Domains Mined:** `2` distinct domains discovered outside the seed whitelist
- **Total Verified Articles (Score $\ge$ 80):** Closed-List = `0`, Extended Open-Web = `0`
- **Mean Credibility Score:** Closed-List = `14.7/100`, Extended Open-Web = `14.3/100`