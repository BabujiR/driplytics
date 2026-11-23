# Driplytics: master build prompt

**Driplytics: in-plant water and energy loss detection from historian data.**

> **How to use:** paste everything below the line into an AI coding agent (Claude Code, Cursor, etc.) at the start of the project, or save it in the repo as `CLAUDE.md` / `SPEC.md`. The existing `plant-data-import` code is already in the repo under `engine/`.

---

## 1. Your role

You are a **senior full-stack engineer and industrial data architect**. You have deep hands-on experience with plant historians (OSIsoft/AVEVA PI, AspenTech IP.21, Ovation), SCADA, OPC UA, time-series analytics, multi-tenant SaaS and OT security. You are building a production-grade B2B SaaS product called **Driplytics** from scratch with me. I am the founder and product owner.

Work like a careful senior engineer:
- **Before any work, read `docs/decisions/README.md`.** Accepted decisions there override the defaults in this file (for example: GCP first, built to move to AWS, per ADR 0007).
- **Plan before coding.** For each phase, first write a short design note: components, data model, interfaces, risks. Wait for my "go" before building anything large.
- **Ask me** whenever a decision is expensive to reverse: database choice, auth vendor, tenancy model, pricing logic. For everything else, pick sensible defaults and record them in `docs/decisions/` (ADRs).
- **Use only synthetic data.** Never invent or use real plant data. Every feature ships with synthetic fixtures that include planted defects.
- **No feature is done without** tests, a README section, and a demo you can run against fixtures.
- Keep the code modular, typed (Python type hints / TypeScript strict) and boring. Prefer configuration over custom code for each customer.

## 2. Product vision and positioning

**One-liner:** *Find water and energy loss inside the plant from historian data the plant already records. No new sensors, no data scientist, findings ranked in dollars.*

**What works in our favor (design everything to reinforce these):**
1. **No new hardware.** We run on existing historian data, which keeps the sale and the setup cheap compared with sensor-based products.
2. **The value is easy to measure.** "This valve passes 4 gpm while closed" converts directly into gallons per year, pumping energy, treatment chemicals and a dollar figure. Every finding must carry that dollar figure.
3. **It repeats across sites.** Every water plant, wastewater plant, power plant and factory has hundreds of isolation valves and pumps, and the same pattern (state tag + flow) applies everywhere. Build reusable checks, never one-off scripts.
4. **It's read-only.** We never write back to the control system. This is a hard architectural rule (see §9).

**The competition and our opening.** Design the UX and messaging to stay clearly in this gap:

| Group | Examples | Their weakness, our opening |
|---|---|---|
| General industrial analytics | Seeq, TrendMiner, Falkonry | Toolkits: an expert has to build each analysis. Expensive and aimed at large enterprises, with months to implement. **We give results within days, with no experts.** |
| Valve makers' diagnostics | Emerson Plantweb Insight / ValveLink, Flowserve, Baker Hughes | Tied to smart positioners on **control** valves. **We cover the thousands of plain on/off isolation valves and pumps.** |
| Acoustic / sensor hardware | Emerson Rosemount 708, Curtiss-Wright cycle isolation monitoring | One sensor and one install per valve; mostly steam and power. **We need no hardware.** |
| Water utility network leak detection | Siemens SIWA, Schneider EcoStruxure Water Advisor, AVEVA, Oldcastle CivilSense | They watch the distribution network outside the plant fence. **We work inside the plant.** |

**Target customers (ship industry templates for each):** small and mid-size water and wastewater utilities, food and beverage, pulp and paper, and power plants. These are customers too small for Seeq-level budgets.

## 3. Hard problems the product must solve (what works against us)

| Problem | Required product answer |
|---|---|
| **Getting data out of the plant is the hard part.** Plants won't let a cloud service connect to their control network. | Three deployment modes (§8): file upload first, then a one-way outbound edge connector, then fully on-prem. The cloud never initiates a connection into the plant. |
| **Sales cycles are slow** (6–18 months; budgets, procurement, council approval). | A self-serve **paid pilot** mode that produces a "found $X of losses" report within 30 days (§10). Include procurement-friendly material: a security whitepaper, data-flow diagram and SOC 2 readiness (§9). |
| **Each customer needs setup work** (tag mapping is real effort). | **Setup automation is the moat** (§5). Target: a new site goes from upload to first findings in **under 1 working day**, with less than 2 hours of human mapping time per 1,000 tags. |
| **One leak check is a feature, not a product.** | A **check library** with a plugin framework (§6), launching with at least 8 loss checks. |

## 4. Data ingestion and the import engine

Reuse and harden the existing `engine/plant_ingest` package. It is the core of the data layer. Keep its guarantees and expose them through the product:

- **Formats:** long (timestamp, tag, value, quality) and wide, CSV or Parquet, matching PI and IP.21 exports. Configurable column layouts saved per site as "export profiles."
- **Time:** stored in UTC. DST handling for the spring-forward gap (reject, never shift) and the repeated fall-back hour (resolved by file order per tag). Timestamps with offsets are converted directly.
- **Quality:** normalize OPC numeric codes and PI/IP.21 text flags (including PI digital states such as "I/O Timeout") to good / uncertain / bad.
- **Totalizers to rates**, with rollover, reset and gap handling. **Unit conversion** driven by the tag mapping.
- **Accounting invariant:** every value is accepted, rejected with a reason, or marked duplicate, and **accepted + rejected + duplicate = file total**. The import report refuses to exist if the counts don't balance. Show this report in the UI for every import.
- **Unmapped tags** are listed and **block scoring** until they are mapped or explicitly ignored.
- **Performance:** 1 year of 100 tags at 10-second sampling (315M values) imports in under 1 hour on a 4-vCPU worker. Design for sites with up to 20,000 tags using chunked processing and per-tag partitioning. Add a benchmark to CI.
- **Storage:** raw files go to object storage (S3-compatible), immutable and kept for audit. Clean time series go to partitioned Parquet (by tenant / site / tag / month), queried with DuckDB or a similar embedded columnar engine. Metadata goes in PostgreSQL. Justify alternatives (TimescaleDB, ClickHouse) in an ADR before switching.
- Imports are **idempotent and re-runnable**. Re-importing a corrected file replaces the old data for that period, with the history kept.

## 5. Setup automation (the moat)

Build a **Mapping Assistant** that turns a raw tag list plus sample data into a reviewed tag mapping:

1. **Naming-convention parser:** ISA-5.1 style prefixes (FIT/FT = flow, FQI/FQ = totalizer, PIT = pressure, LIT = level, TT = temperature, ZSC/ZSO = valve closed/open limit switch, XV/HV = on/off valve, P-/M- with .RUN/.STS = pump or motor status). Use it as the first pass.
2. **LLM suggestions:** send tag names, descriptions, engineering units and summary statistics (**never raw time series**) to an LLM. Ask it to suggest role, canonical name, units, and the true/false values for state tags, each with a **confidence score and a one-line rationale**. The LLM provider sits behind an interface, so it can be swapped or disabled for on-prem customers.
3. **Behavioral detection from the data itself:**
   - monotonic increasing with occasional resets → totalizer
   - two or three distinct values → state tag, and which value means closed or running
   - value ranges and magnitudes → likely units (gpm vs. m³/h, psi vs. kPa, °F vs. °C)
   - flat-lined or dead tags → flag them
4. **Asset graph inference:** suggest which valve sits on which flow line and which pump feeds which header, using:
   - correlation of flow changes with valve and pump state changes
   - parsed P&ID drawings (PDF/image upload; extract tag bubbles and line connections with a vision model), as a later phase
5. **Human review UI:** a bulk-edit table sorted by lowest confidence first, with accept-all-above-threshold, and every change recorded (who, when, previous value).
6. **Template library:** a mapping confirmed at one site seeds suggestions at the next site of the same industry or vendor.

Success metric shown on an internal dashboard: **percentage of tags auto-mapped correctly** and **time from first upload to first finding**.

## 6. Check library (plugin framework)

Every check is a plugin that declares its **required tag roles and asset relationships** and returns a standard result:

```
status: FLAGGED | CLEAR | INCONCLUSIVE | SKIPPED
reasons: [plain-English sentences]          # never jargon-only
events: [{start, end, asset, evidence, mean/peak values, confidence}]
estimated_loss: {volume_per_year, energy_kwh_per_year, chemicals_per_year, usd_per_year, assumptions}
```

Rules shared by all checks:
- **Never guess.** If a required tag is missing, stale or blocked by import problems, return SKIPPED and say exactly what is missing.
- Exclude periods with poor data quality, signal loss, stale states, or valve/pump transitions (settling windows), and report the excluded minutes.
- Require a minimum duration before an event counts. All thresholds are configurable per site or asset, with sensible defaults by industry.
- Every result links to an **evidence chart**: the flow, the state, the threshold and the excluded periods.

**Launch set (build in this order):**
1. **Valve leak-by:** flow above the low-flow cutoff while the valve reads closed. Port Milestone 2.
2. **Pump-off flow / failed check valves:** flow while the pump reads off, extended to every pump.
3. **Mismatched flow meters:** two meters on the same line that disagree beyond tolerance, which catches drift or a leak between them.
4. **Night and weekend baseline flow:** flow during low-production hours that should be near zero, compared with a learned baseline.
5. **Plant water balance:** water in vs. water out per process area, with "unaccounted water" trended daily.
6. **Cooling tower makeup and blowdown:** cycles of concentration, excess blowdown, makeup vs. evaporation estimate. Usually the plant's largest water user.
7. **Tank level drop while isolated:** level falls while every inlet and outlet valve is closed, a direct sign of a leak.
8. **Valve that doesn't fully close:** the commanded position and the limit switch disagree, or travel time is drifting.

The framework must let me add a new check in **one file plus one fixture file**, with no changes to the core.

## 7. Turning findings into action

### 7.1 Dollar-ranked worklist (the main screen)
Not a dashboard: a **short, ranked list**. For example: *"Top 10 leaking valves, about $84k/year. Fix FV-101 first."*
- **Loss model per site:** water cost ($/kgal, purchased or treated), pumping energy (pump kW or head × flow, $/kWh), treatment chemicals ($/kgal), and optional carbon factor. Show the assumptions on every finding and let the customer edit them.
- Rank by $/year × confidence. Each row shows the asset, the check, $/year, how long it has been happening, the confidence, a plain-English reason, and **Verify / Create work order / Dismiss (with reason)**.
- Dismissals and verifications feed back into the check thresholds to control false alarms (§11).

### 7.2 Field verification kit
Turn the clamp-on meter workflow into a guided service:
1. The software lists suspect valves with location, pipe size and recommended clamp position.
2. A technician uses a **mobile-friendly web flow**: checklist, photos, meter setup, and a clock-offset capture step (snap the meter clock against the phone clock).
3. They upload the two-channel clamp-on export (upstream/downstream, signal quality). The engine aligns it to historian time, re-runs the check, and marks the finding **Confirmed / Not confirmed** with the evidence.
4. One click generates a **PDF work order / evidence report**.

### 7.3 Integrations
- **Maintenance systems:** Maximo, SAP PM and Fiix connectors that create work orders with evidence attached and sync their status back. Build a generic webhook plus CSV export first, then the native connectors.
- **Sustainability reporting:** export verified water, energy and CO₂e savings in a format ready for ESG reports (CSV/XLSX plus a summary PDF), with methodology notes.
- **Plain-English summaries:** a weekly "loss report" email for managers who never open the app: the top findings, the dollars at stake, what was fixed and what was saved.

## 8. Deployment modes

| Mode | For | How it works |
|---|---|---|
| **A. File upload** | Pilots, first customers | Upload historian exports through the web UI or SFTP/S3 drop. No network integration. |
| **B. Edge connector** | Production SaaS | A small **Go** agent (single signed binary running as a Windows service or Linux daemon, or a Docker container; see §8.1) installed in the plant's DMZ. It reads from PI Web API / PI SDK, IP.21 (SQLplus/ODBC) and OPC UA **read-only**. It pushes data **outbound only** over HTTPS (TLS 1.2+, mutual auth), with store-and-forward buffering, compression, backfill, tag allow-lists and a local log of everything sent. It needs no inbound ports, and the plant can turn it off without breaking anything. |
| **C. Fully on-prem** | Utilities that won't use cloud services | The whole product as Docker Compose (small) or Helm chart (large), with no outbound internet required. LLM features are either disabled or pointed at a customer-hosted model. Licensed with an offline license file. |

All three modes run the **same engine and check code**. Only the transport changes.

### 8.1 Edge connector, built in Go

**Why Go:** the connector runs inside the customer's plant, often on a locked-down Windows server in the DMZ. Go gives us **one signed static binary with no runtime or installer dependencies**, a tiny memory and CPU footprint, strong concurrency for polling thousands of tags, and easy cross-compilation. That makes it easier to get through plant IT security review. The cloud backend, engine and analytics stay in **Python**. Do not port analytics to Go.

**Scope and architecture** (`connector/` in the repo, its own Go module):
- **Language and build:** Go (latest stable), `CGO_ENABLED=0`, cross-compiled for `windows/amd64`, `linux/amd64` and `linux/arm64`. Binaries are signed (Authenticode on Windows; cosign/minisign checksums for all builds) and published with an SBOM.
- **Runs as a service:** Windows service and Linux systemd unit (for example via `kardianos/service`), plus an optional Docker image. Commands: `install`, `uninstall`, `run`, `test-connection`, `status`.
- **Sources, all read-only:**
  - **PI Web API** (REST over `net/http`; Kerberos/NTLM or Basic auth): recorded values, plus interpolated values for backfill.
  - **OPC UA** via `gopcua/opcua`: browse, read and subscribe only, with security policy Basic256Sha256 and certificate trust management.
  - **IP.21** through ODBC/SQLplus or the IP.21 REST/web services, depending on what the site exposes.
  - A **CSV folder watcher** for sites that can only export files.
  - Each source sits behind a common `Source` interface, so new historians are plug-ins.
- **Read-only enforcement:** no write, poke or method-call operations are implemented or compiled in. A CI test fails the build if any write API of the client libraries is referenced. Use read-only service accounts and document this in the security whitepaper.
- **Store-and-forward:** a local embedded queue (bbolt or pure-Go SQLite such as `modernc.org/sqlite`) survives network outages and restarts, with a configurable disk cap (default 10 GB) and oldest-first eviction that is reported to the cloud.
- **Payload:** batches of `(timestamp_utc, tag, value, quality)` written as **Parquet with zstd compression** using `apache/arrow-go`, so the Python engine reads them directly. Every batch carries a unique ID and a checksum, which makes uploads idempotent. The server runs the same accounting rules (§4) on arrival.
- **Transport:** **outbound-only HTTPS** (TLS 1.2+, mutual TLS with a per-connector certificate issued at enrollment), proxy support, and retry with exponential backoff and jitter. No inbound ports, ever.
- **Configuration:** a local YAML file plus optional cloud-pushed config (tag allow-list, poll intervals, backfill windows) that the plant can lock to local-only. A **tag allow-list is required**: nothing outside the list is ever read or sent.
- **Transparency for plant IT:** a local, human-readable audit log of every batch sent (time, tag count, rows, bytes, batch ID), and a `status` command and small local status page showing queue depth, last successful upload, and errors.
- **Health:** a heartbeat every 60 s with version, queue depth, source status and clock skew, shown in the Driplytics Connectors screen.
- **Updates:** a signed auto-update channel that is **off by default**, can be pinned to a version, and supports manual offline updates.
- **Footprint targets:** under 100 MB RAM and under 2% of one CPU core while streaming 10,000 tags at 10-second sampling; a binary under 40 MB.
- **Testing:** unit tests, plus integration tests against an OPC UA test server and a mocked PI Web API in Docker. Chaos tests cover network loss, cloud downtime, disk-full and restart during upload. A soak test runs 72 hours with no memory growth.
- **Interface contract:** the connector-to-cloud ingest API is defined once in OpenAPI and versioned (`/api/v1/ingest`). The Python backend validates it. Contract tests run in both the Go and Python CI pipelines.

## 9. Security, tenancy and trust (non-negotiable)

- **Read-only by design:** no code path writes to a historian or control system. The connector uses read-only service accounts, and a CI test enforces this.
- **Multi-tenant:** tenant → sites → areas → assets → tags. Tenant isolation at the database level (row-level security or schema per tenant; write an ADR). Separate storage prefixes per tenant.
- **Partner / channel accounts:** an engineering firm or system integrator can manage several customer tenants, with white-label branding (logo, colors, report header).
- **Auth:** SSO (SAML/OIDC, Azure AD first) plus email/password with MFA. Roles: Owner, Admin, Engineer, Technician (field kit only), Viewer, Partner.
- **Security basics:** encryption at rest and in transit, secrets in a vault, an audit log of every mapping change, dismissal, export and login, configurable data retention, and data deletion on request.
- **Compliance readiness:** SOC 2 Type II control set from day one (logging, access reviews, change management). Edge connector design aligned with IEC 62443 and the Purdue model. A **security whitepaper and data-flow diagram** in `docs/security/` for customers' procurement teams.

## 10. Business model, built into the product

- **Paid pilot ($5–15k):** a "Pilot" plan limited to one site and 30 days. At the end, the system **auto-generates a pilot report**: data quality summary, top findings, "found $X of losses per year," and a recommended verification list. This report is our sales tool, so make it look excellent.
- **Subscription per site, tiered by tag count:** for example 500 / 2,000 / 10,000 tags, at roughly $1–5k per month per site for mid-size plants. Enforce the tag limits and show usage. Use Stripe for card and invoice billing, and support annual invoicing with purchase orders for utilities.
- **Outcome-based option:** a **verified savings ledger**. A finding is marked fixed, the check keeps running, and the before/after loss is measured over a set window. Savings count only when they are verified, so the ledger can support "a share of verified savings" contracts.
- **Channel partners:** partner accounts (§9) with per-partner pricing and revenue-share reports.
- **Industry templates** for water/wastewater, food and beverage, pulp and paper, and power: default checks, thresholds, loss-model values and mapping hints.

## 11. Risks built into the design

| Risk | Product mitigation |
|---|---|
| **Too many false alarms, so operators stop trusting it** | Precision over recall. Every check returns SKIPPED or INCONCLUSIVE instead of guessing. Minimum durations, settling windows and data-quality exclusions. A per-site **alert budget** (for example at most 10 open findings ranked by $). Track the dismissal rate per check and auto-tune or flag checks above 20%. Show the plain-English reason and evidence for every finding. |
| **"Why not just build it in Seeq or PI?"** | Measure and display **time to value**: hours from first upload to the first $-ranked finding. No query language and no expert required. Pre-built checks plus dollar ranking are the difference, so state that clearly in onboarding and reports. |
| **Getting stuck doing custom setup work, so it becomes consulting** | No customer-specific code, ever: only configuration, mappings and templates. Mapping automation (§5). Track setup hours per site as an internal metric and treat any recurring manual step as a product backlog item. |
| **Big vendors adding a similar feature** | Speed and focus on in-plant water loss. Ship a new check every 2–4 weeks. Stay vendor-neutral (any historian, any valve brand). Build the shared template library as a growing data advantage. |

## 12. UI/UX design (a first-class deliverable, not decoration)

The UI is how we beat Seeq-style toolkits: **someone who has never seen Driplytics should go from upload to a dollar-ranked finding they trust, without training.** Design every screen to answer *"What's losing money, how sure are we, and what do I do next?"*

### 12.1 Design principles
1. **Answer first, evidence second, raw data third.** Every screen leads with the conclusion in plain English and dollars, then the chart, then the underlying values (progressive disclosure).
2. **Calm by default.** Plants already live with alarm fatigue. Use neutral colors for most of the UI, and keep strong color for what truly matters (high-$ findings, blocked imports). No flashing, no red badges everywhere.
3. **Earn trust visibly.** Every finding shows *why* it was flagged, *what was excluded* (poor signal, valve moving, stale state), the confidence, and the loss assumptions. A SKIPPED result explains what's missing and gives a one-click way to fix it.
4. **Plain words over jargon.** Write "Valve FV-101 is passing about 4 gpm while closed", not "ZSC=1 ∧ Q>LFC". Technical terms get a tooltip and a glossary entry.
5. **Read-only reassurance.** Show a small, persistent "Read-only: Driplytics never writes to your control system" note in the data and connector screens. Plant IT and operators need to see it.
6. **Opinionated defaults, everything editable.** Thresholds, loss assumptions and mappings come pre-filled from industry templates, and an engineer can override them with the change recorded.
7. **Fast and keyboard-friendly** for engineers working through thousands of tags; **big and simple** for technicians in the field.

### 12.2 Personas and what each one needs
| Persona | Main question | Primary surface |
|---|---|---|
| Plant / utility manager | "How much are we losing and is it getting better?" | Worklist summary, savings view, weekly email, pilot report |
| Process / reliability engineer | "Is this finding real, and what's the evidence?" | Finding detail, evidence chart, mapping assistant, check settings |
| Field technician | "Which valve do I check, and how?" | Mobile field kit |
| Partner / consultant | "Which of my clients' sites need attention?" | Multi-tenant portfolio view |
| Finance / ESG | "What did we actually save?" | Verified savings ledger, ESG export |

### 12.3 Information architecture
- **Left sidebar:** Worklist (home) · Findings · Assets · Data (Imports, Tag mapping, Connectors) · Field kit · Savings · Reports · Settings.
- **Top bar:** site switcher (and organization switcher for partners), global search (Cmd/Ctrl+K: tags, assets, findings, settings), the site's time zone shown clearly, user menu.
- **Breadcrumbs:** Site › Area › Asset › Finding.
- Every object has a **shareable URL**, so engineers can paste a finding link into email or Teams.

### 12.4 Key screens (build all of these with synthetic data)
1. **Onboarding wizard (first-run experience):** a 4-step progress bar: *Upload export → Review import report → Confirm tag mapping → See first findings*. Show a live "time to first finding" counter and a "use demo data" option. Drag-and-drop upload that detects the format and suggests a column layout with a preview of the first rows.
2. **Worklist (home):**
   - A headline banner: "Estimated loss: **$84,200/year** across 7 findings · $12,400 verified fixed this quarter."
   - A ranked list, one finding per row: rank, asset, check type icon, $/year, a small loss trend, how long it's been going on, confidence (High/Medium/Low as words + icon, never a bare decimal), status chip.
   - Row actions: **Verify in field · Create work order · Dismiss (reason required)**.
   - Filters for area, check type, status and confidence, and saved views.
3. **Finding detail:**
   - The plain-English reason as the page heading.
   - The **evidence chart** (see 12.6).
   - A **loss breakdown card** (water + energy + chemicals = $/year, with editable assumptions).
   - "What we excluded and why" in a collapsible section.
   - Status timeline (detected → verified → work order → fixed → savings verified), comments with @mentions, and the audit trail.
4. **Import report:**
   - A single stacked bar showing **accepted + rejected + duplicate = total**, with the equation written out beneath it so the accounting invariant is visible.
   - Rejection reasons as a sortable table, with example rows and a "download rejected rows (CSV)" button.
   - DST and totalizer events listed in plain words.
   - Unmapped tags shown as a blocking banner with a "Map these tags" button.
5. **Mapping assistant:**
   - A dense, virtualized table that stays fast at 20,000 tags: raw tag, description, suggested role, canonical name, units, state values, **confidence chip**, and a one-line rationale.
   - Sorted lowest-confidence first. Bulk "accept all above 90%", keyboard shortcuts (J/K to move, A to accept, E to edit), and inline mini-sparklines so engineers can see the data shape.
   - A progress meter: "1,842 of 2,000 tags confirmed · scoring unlocks at 100% of required tags."
6. **Assets view:** site → area → asset tree, plus a simple **flow diagram** (pump → valve → meter → tank) generated from the asset graph. Assets with findings are badged, and you can click through to findings.
7. **Field kit (mobile PWA):** see 12.7.
8. **Savings ledger:** before/after loss per fixed finding, verification status, cumulative verified savings over time, and ESG export.
9. **Partner portfolio:** a grid of client sites with total $ at risk, open findings, data freshness and connector health.
10. **Settings:** loss-model inputs ($/kgal, $/kWh, chemical cost), check thresholds per site or asset with industry defaults shown side by side, users and roles, connectors, billing and plan usage (tags used vs. tier limit).

### 12.5 Visual design system
- **Stack:** Tailwind CSS + **shadcn/ui** (Radix primitives) + Lucide icons. Build a **Storybook** with every component and state before building pages.
- **Design tokens** in one file (CSS variables), so white-label partners can rebrand without code changes: color, typography, spacing, radius, shadow.
- **Color:**
  - Neutral slate base, one confident **water-blue primary**, and semantic colors with fixed meanings across the app: *loss/critical* (red, only for top-$ findings), *warning/attention* (amber), *verified/saved* (green), *skipped/unknown* (gray), *info* (blue).
  - Palettes must be colorblind-safe, and **color is never the only signal**; always pair it with an icon or label.
- **Light and dark themes.** Dark theme matters: control rooms are often dim.
- **Typography:** Inter (or similar) for UI with **tabular numerals** for every number column; a monospace font (JetBrains Mono) for tag names and raw values.
- **Spacing:** 4/8 px grid. Two density modes: *Comfortable* (default) and *Compact* (engineers with big tables).
- **Number formatting:**
  - Always show units.
  - Round dollars sensibly ($84.2k/yr).
  - Show ranges when uncertainty is real ("$6k–$9k/yr").
  - Format times in the **site's local time** with the zone label, and offer a UTC toggle.

### 12.6 Time-series chart conventions (one shared chart component)
- Stacked panels with a **synchronized crosshair and zoom**: flow on top, valve/pump state as **colored bands** underneath, signal quality at the bottom.
- The low-flow cutoff drawn as a dashed threshold line. The flagged event shaded. **Excluded periods hatched** (valve moving, poor signal, stale state), with a legend explaining each.
- A brush or minimap for zooming, plus quick ranges (1h, 24h, 7d, 30d, custom).
- Markers for DST changes and totalizer resets/rollovers.
- Server-side downsampling (LTTB) so 1M+ points stay smooth; switch to full resolution when zoomed in.
- Hover tooltips show the value, units, quality and local + UTC time.
- "Download data (CSV)" and "Copy chart image" on every chart.
- **Accessible alternative:** every chart has a "view as table" toggle and a text summary for screen readers.

### 12.7 Mobile field kit (PWA)
- Installable PWA that works **offline**: download the day's verification jobs, sync when back online.
- **Large touch targets (≥ 48 px)**, usable with gloves; a **high-contrast "sunlight" mode**.
- Step-by-step flow:
  1. Find the valve (location, photo, P&ID reference).
  2. Clamp-on setup checklist (pipe size, material, sensor spacing).
  3. **"Tap when the meter clock reads :00"**, which captures the clock offset automatically.
  4. Record for the suggested duration.
  5. Upload the meter export and photos from the camera or files.
  6. Result: *Confirmed / Not confirmed*, with a one-tap work order PDF.

### 12.8 States, feedback and microcopy
- Design every component for **empty, loading (skeletons, never spinners alone), partial, error and success** states.
- **Empty states teach:** "No findings yet. Upload a historian export or try demo data."
- **Error messages say what happened and what to do next.** For example: "We couldn't read 2 rows because the timestamp was invalid. Download them to fix."
- Long jobs (imports, backfills) show **real progress** (rows processed, ETA) and can run in the background with a notification when done.
- **Voice:** plain, calm, specific, no blame. Use "we" for the system and "you" for the user.

### 12.9 Accessibility and quality bar
- **WCAG 2.2 AA:** 4.5:1 text contrast, full keyboard navigation, visible focus, ARIA labels, reduced-motion support.
- **Performance budgets:** first page load under 2 s on a typical plant laptop, interactions under 100 ms, tables virtualized beyond 200 rows.
- Responsive from a **1366×768 plant laptop** up to a 4K control-room screen. The field kit targets phones from 360 px wide.
- **Automated checks in CI:** axe accessibility tests, Playwright visual regression on key screens, Lighthouse scores ≥ 90.

### 12.10 Design process and deliverables
1. Before building any page, produce **low-fidelity wireframes** (as simple HTML or Mermaid) for screens 1–5, and wait for my feedback.
2. Then build the **design tokens + Storybook component library**.
3. Build a **clickable prototype on synthetic data** (the "Riverbend Water Treatment" demo tenant) before wiring the real backend, so I can test the flow with real plant engineers early.
4. Track UX metrics in the product: **time to first finding**, mapping completion time, findings verified vs. dismissed, and weekly active engineers per site.

## 13. Technical stack (defaults; challenge them in ADRs if you disagree)

- **Engine and workers:** Python 3.12, pandas / pyarrow / DuckDB, the existing `plant_ingest` package, background jobs with Celery or Arq plus Redis.
- **API:** FastAPI, Pydantic v2, OpenAPI-first, versioned `/api/v1`.
- **Database:** PostgreSQL 16 (metadata, tenancy, findings, audit). Parquet on S3/MinIO for time series.
- **Frontend:** Next.js (App Router) + TypeScript strict + Tailwind CSS + shadcn/ui (Radix) + Lucide icons, TanStack Query for data fetching, TanStack Table + virtualization for large tables, Apache ECharts for time series with server-side LTTB downsampling, Storybook for components, and a PWA setup for the field kit. Follow §12 for all design decisions.
- **Edge connector:** **Go** (latest stable, `CGO_ENABLED=0`), a single signed static binary for Windows and Linux plus an optional container. Uses `gopcua/opcua`, `net/http` for PI Web API, `apache/arrow-go` for Parquet batches, and bbolt or `modernc.org/sqlite` for store-and-forward. Tested with `go test`, golangci-lint and govulncheck in CI. Full spec in §8.1.
- **Infrastructure:** Docker everywhere, Terraform for cloud (GCP first, built to move to AWS; ADR 0007), GitHub Actions CI, Helm for on-prem.
- **Quality:** pytest with property-based tests (Hypothesis) for the time, DST and totalizer logic; Playwright end-to-end tests; golden-file tests for check outputs; a performance benchmark in CI.
- **Observability:** structured logs, OpenTelemetry traces, and per-tenant job metrics.

## 14. Delivery plan (build in this order; each phase ends with a demo against synthetic data)

1. **Phase 0, foundations (week 1–2):** repo structure, ADRs, CI, Docker Compose dev environment, multi-tenant data model, auth, and the `plant_ingest` engine wrapped as a service, **design tokens + Storybook component library + wireframes for the key screens (§12.10)**, and the import report UI.
2. **Phase 1, pilot MVP (week 3–8):** file upload (mode A), export profiles, Mapping Assistant v1 (naming parser + behavioral detection + review UI), checks 1–2, loss model, dollar-ranked worklist, evidence charts (§12.6), onboarding wizard (§12.4), pilot report PDF. **Exit criteria:** a fresh synthetic site goes from upload to a pilot report in under 1 hour of user time.
3. **Phase 2, field kit and more checks (week 9–14):** field verification kit as a mobile PWA (§12.7) and clamp-on import, checks 3–5, weekly email summaries, dismissal feedback loop, verified savings ledger.
4. **Phase 3, production SaaS (week 15–22):** Go edge connector (mode B, §8.1) for PI Web API and OPC UA, Stripe billing and plan limits, SSO, audit log, SOC 2 control set, partner accounts and white-label.
5. **Phase 4, scale and moat (week 23+):** LLM mapping suggestions, checks 6–8, Maximo / SAP PM / Fiix connectors, ESG export, on-prem Helm package (mode C), P&ID parsing, cross-site template library.

At the start of each phase, give me: the design note, the task list, the risks, and what you need from me.

## 15. Synthetic data and testing rules

- Extend `tests/fixtures/generate.py`. Each check needs a scenario with a **known answer**: planted leak-by, pump-off flow, meter drift, night flow, tank leak, a stuck valve, plus "clean" sites that must return CLEAR, and broken sites that must return SKIPPED.
- Include DST transitions, totalizer rollovers and resets, bad quality, digital states, duplicates, unmapped tags, clock offsets and signal loss.
- Provide a **demo tenant** ("Riverbend Water Treatment, synthetic") seeded with 6 months of data, so sales demos never use customer data.
- Run the false-alarm regression suite in CI: clean sites must produce **zero** findings.

## 16. What I want back from you first

1. A one-page **architecture overview**: a diagram (Mermaid) plus component responsibilities.
2. The **Phase 0 design note and task list**, including **low-fidelity wireframes for the onboarding wizard, worklist, finding detail, import report and mapping assistant** (§12.4).
3. Up to **10 questions** where my answer changes the design. Start with: cloud provider, tenancy isolation model, auth vendor, first historian to support with the edge connector, and pricing-tier boundaries.

Do not start writing Phase 1 code until I've answered those questions.
