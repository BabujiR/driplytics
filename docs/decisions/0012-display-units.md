# 0012. Display units: a per-site setting, defaulting to US customary

- **Status:** Accepted
- **Date:** 2026-11-22
- **Answers:** Q7 in `docs/questions.md`

## Decision
Storage stays in each tag's canonical target unit. Each site has a `display_units` setting: **US customary** (gpm, gal, MGD, psi, ft, °F) by default for US sites, or **SI** (m³/h, m³, kPa, m, °C). The API returns values with explicit units; the UI converts for display using one shared formatter. Exports and reports state their units.
