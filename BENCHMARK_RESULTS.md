# Phase II Empirical Evaluation: Closed-List vs. Open-Web Discovery

**Evaluation Timestamp:** 2026-09-26 18:08:14  
**Search Engine:** DuckDuckGo News (`ddgs`) | **Extractor:** Trafilatura  

### Comparative Performance Table

| Query ID | Topic / Category | Closed Articles | Open Articles | Closed Domains | Open Domains | Discovered Unregistered Domains | Verified Yield (Open) | Latency (Closed/Open) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1** | Artificial Intelligence | 0 | 20 | 0 | 16 | **+16** | 0 (0.0%) | 1.92s / 9.82s |
| **Q2** | Geopolitics & Security | 0 | 20 | 0 | 18 | **+18** | 13 (65.0%) | 1.24s / 8.46s |
| **Q3** | Space & Astrophysics | 0 | 20 | 0 | 12 | **+12** | 8 (40.0%) | 2.08s / 9.62s |
| **Q4** | Energy & Climate Policy | 1 | 21 | 1 | 20 | **+19** | 10 (47.6%) | 2.45s / 8.75s |
| **Q5** | Semiconductors & Trade | 0 | 20 | 0 | 19 | **+19** | 5 (25.0%) | 2.05s / 8.7s |
| **Q6** | Regional Infrastructure | 1 | 21 | 1 | 15 | **+15** | 10 (47.6%) | 2.29s / 8.58s |

### Aggregate Metrics Summary

- **Total Articles Retrieved:** Closed-List = `2`, Extended Open-Web = `122` (`+120` articles)
- **Domain Coverage Expansion:** `2` $\rightarrow$ `100` unique domains (**+4900.0% expansion**)
- **Unregistered Open-Web Domains Mined:** `99` distinct domains discovered outside the seed whitelist
- **Total Verified Articles (Score $\ge$ 80):** Closed-List = `0`, Extended Open-Web = `46`
- **Mean Credibility Score:** Closed-List = `15.2/100`, Extended Open-Web = `59.6/100`