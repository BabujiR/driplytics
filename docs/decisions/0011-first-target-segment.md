# 0011. First target segment: municipal water and wastewater

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q6 in `docs/questions.md`

## Decision
- **Primary:** municipal water and wastewater treatment plants. The demo tenant ("Riverbend Water Treatment, synthetic"), the first industry template (default checks, thresholds, loss-model values, tag-naming hints) and the marketing language target them.
- **Secondary, in parallel for sales:** food and beverage plants, which buy faster and often run PI. Their template follows in Phase 2.
- Power, and pulp and paper later.

## Consequences
Loss-model defaults use water-utility costs ($/kgal treated, pumping $/kWh, chemicals $/kgal), all editable per site.
