# 0015. Worklist shows the top 10 findings by default

- **Status:** Accepted
- **Date:** 2026-11-22

## Decision
The worklist shows the **top 10 open findings ranked by $/year × confidence**, with a clear "Show all (N)" control. Low-confidence findings are hidden by default but counted ("3 low-confidence findings hidden"). The cap is a per-site setting (an "alert budget").

## Consequences
Keeps the product calm and trustworthy, the main defense against alarm fatigue. Dismissal rates per check are tracked to tune thresholds.
