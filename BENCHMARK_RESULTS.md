# Phase II Empirical Evaluation: Closed-List vs. Open-Web Discovery

**Evaluation Timestamp:** 2026-09-26 19:22:01  
**Search Engine:** DuckDuckGo News (`ddgs`) | **Extractor:** Trafilatura  

### Comparative Performance Table

| Query ID | Topic / Category | Closed Articles | Open Articles | Closed Domains | Open Domains | Discovered Unregistered Domains | Verified Yield (Open) | Latency (Closed/Open) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1** | Artificial Intelligence | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 2.48s / 6.51s |
| **Q2** | Geopolitics & Security | 0 | 14 | 0 | 11 | **+11** | 0 (0.0%) | 0.66s / 11.56s |
| **Q3** | Space & Astrophysics | 0 | 10 | 0 | 5 | **+5** | 0 (0.0%) | 2.08s / 11.27s |
| **Q4** | Energy & Climate Policy | 1 | 1 | 1 | 1 | **+0** | 0 (0.0%) | 2.49s / 7.75s |
| **Q5** | Semiconductors & Trade | 0 | 0 | 0 | 0 | **+0** | 0 (0.0%) | 2.03s / 6.0s |
| **Q6** | Regional Infrastructure | 2 | 12 | 2 | 8 | **+8** | 1 (8.3%) | 2.47s / 13.16s |

### Aggregate Metrics Summary

- **Total Articles Retrieved:** Closed-List = `3`, Extended Open-Web = `37` (`+34` articles)
- **Domain Coverage Expansion:** `3` $\rightarrow$ `25` unique domains (**+733.3333333333333% expansion**)
- **Unregistered Open-Web Domains Mined:** `24` distinct domains discovered outside the seed whitelist
- **Total Verified Articles (Score $\ge$ 80):** Closed-List = `0`, Extended Open-Web = `1`
- **Mean Credibility Score:** Closed-List = `15.2/100`, Extended Open-Web = `34.3/100`