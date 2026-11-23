# plant-ingest: historian importer and valve leak-by check

This package has two Python modules that work only from data the plant already records:

* **Milestone 1, historian importer:** reads PI and IP.21 style exports (long or wide, CSV or Parquet) and turns them into a clean UTC pandas DataFrame plus an import report that accounts for every input value.
* **Milestone 2, clamp-on import and leak-by check:** loads a two-channel portable ultrasonic meter export, lines it up with historian time, joins pump and valve states, and flags flow while a valve reads closed or a pump reads off. Every flag comes with a plain-English reason.

All data in this repo is synthetic.

```
src/plant_ingest/
  constants.py   Outcome / Reason / Quality / Role enums (reason priority = declaration order)
  mapping.py     tag-mapping file loader + validation
  readers.py     long / wide, CSV / Parquet -> one raw long shape; chunked iteration
  timeconv.py    timestamp parsing, local -> UTC, DST (spring gap + fall-back repeated hour)
  quality.py     OPC numeric / PI / IP.21 quality -> good|uncertain|bad; PI digital states
  units.py       linear unit conversion (flow, volume, pressure, level, temperature)
  totalizer.py   counter -> rate with rollover, reset and gap handling
  importer.py    the pipeline; import_historian_export() and import_large_file()
  report.py      ImportReport (refuses to exist if counts don't balance)
  clampon.py     clamp-on export reader, clock-offset correction, snap to 10 s grid
  states.py      pump/valve state onto the grid (as-of join, staleness, settling window)
  leakby.py      the leak-by rule and plain-English reasons
tests/           pytest suite (53 tests) + fixtures/generate.py (synthetic data with planted defects)
scripts/benchmark.py   1-year x 100-tag throughput check
```

## Quick start

```bash
pip install -e ".[test]"
python tests/fixtures/generate.py          # (re)build synthetic fixtures
pytest -q
python -m plant_ingest import tests/fixtures/data/historian_long.csv \
       --mapping tests/fixtures/data/tag_mapping.csv --out out/
python -m plant_ingest leakby tests/fixtures/data/leakby_historian.csv tests/fixtures/data/clampon_export.csv \
       --mapping tests/fixtures/data/tag_mapping.csv --valve fv101_closed --pump pump_201_running \
       --cutoff 1.0 --clock-offset 45 --clampon-layout tests/fixtures/data/clampon_layout.json
docker build -t plant-ingest . && docker run --rm plant-ingest      # runs the tests
```

Python API:

```python
from plant_ingest import import_historian_export, ExportLayout, TagMapping
from plant_ingest.clampon import load_clampon_export, ClampOnLayout
from plant_ingest.leakby import run_leak_by_check, LeakByConfig

hist = import_historian_export("export.csv", "tag_mapping.csv")         # -> .values, .report, .ledger
print(hist.report.summary())
clamp = load_clampon_export("meter.csv", ClampOnLayout(skiprows=3), clock_offset_s=45)
result = run_leak_by_check(clamp, hist.values,
                           LeakByConfig(valve_state_tag="fv101_closed", low_flow_cutoff=1.0), hist.report)
result.status, result.reasons, result.events
```

---

## Milestone 1: implementation details

### Output DataFrame

One row per accepted value, sorted by `tag, timestamp_utc`:

| column | meaning |
|---|---|
| `timestamp_utc` | `datetime64[us, UTC]` |
| `tag` | canonical tag from the mapping |
| `raw_tag` | tag as exported |
| `value` | float64, in `unit`. State tags are 0/1: valve **1 = CLOSED**, pump **1 = RUNNING** |
| `unit` | target unit (blank for states) |
| `quality` | `good` or `uncertain` (bad values never get here) |
| `role` | flow / pressure / level / temperature / pump_state / valve_state / other |
| `derived` | True for rates computed from totalizers |

### Tag-mapping file

```csv
raw_tag,canonical_tag,role,source_unit,target_unit,is_totalizer,rollover_max,max_gap_s,state_true,state_false,low_flow_cutoff
FIT-101.PV,inlet_flow,flow,gpm,m3/h,false,,,,,0.23
FQI-101.TOT,inlet_volume_rate,flow,gal,gpm,true,1000000,300,,,
P-201.RUN,pump_201_running,pump_state,,,,,,RUNNING,STOPPED,
FV-101.ZSC,fv101_closed,valve_state,,,,,,1,0,
```

The loader checks the whole file and reports every bad line at once. It catches unknown units, units from different dimensions (for example gpm to psi), totalizers whose source unit isn't a volume or whose target isn't a flow, state tags without `state_true`/`state_false`, and duplicate canonical names.

### Accounting: accepted + rejected + duplicate = file total

Each input value (each **cell** in a wide file) gets exactly one outcome. Reasons are checked in this fixed order, so a value with two problems is counted once, under the first one:

| # | reason | stage | rule |
|---|---|---|---|
| 1 | `unparseable_timestamp` | A | timestamp doesn't parse |
| 2 | `unmapped_tag` | A | tag not in the mapping (also listed in the report, and **blocks scoring**) |
| 3 | `empty_value` | A | blank / whitespace |
| 4 | `bad_quality` | A | quality is Bad (text or OPC code < 64), **or** the value is a PI digital state such as `I/O Timeout` |
| 5 | `non_numeric_value` | A | analog tag, value isn't a finite number |
| 6 | `unrecognized_state` | A | pump/valve value matches neither `state_true` nor `state_false` (case-insensitive; `1.0` matches `1`) |
| 7 | `nonexistent_local_time` | B | local time falls in the spring-forward gap |
| 8 | `conflicting_duplicate` | B | same tag and UTC time but **different** values. All copies are rejected because we can't know which is right |
| - | **duplicate** | B | same tag, UTC time and value. The first copy is accepted and the rest are counted as duplicates |

* **Stage A** checks each row on its own, fully vectorized. Stage A rules are looked up once per distinct tag (category codes) rather than once per row, which matters at 315M rows.
* **Stage B** depends on row order and needs all of a tag's rows: DST resolution, duplicates, totalizers.

`ImportReport.__post_init__` raises `UnbalancedLedgerError` if the counts don't add up, so an unbalanced report can't be produced. With `keep_ledger=True`, `result.ledger` holds `seq, raw_tag, outcome, reason` for every input value. The report also keeps up to 20 example rows per rejection reason so a reviewer can see what was wrong.

**Quality policy:** `uncertain` values (Suspect, Substituted, OPC 64-127) are accepted but tagged, and counted in `accepted_uncertain`. Unknown text flags count as bad. A blank quality defaults to good (configurable), because wide exports usually have no quality column at all.

### Time: UTC and DST

Exports are usually in plant local time with no offset (`ImportConfig.timezone`, default `America/New_York`).

* **Spring forward:** 02:00-02:59 doesn't exist. Those values are rejected as `nonexistent_local_time`, never shifted.
* **Fall back:** 01:00-01:59 occurs twice. The code localizes every row both ways (daylight and standard). For rows where the two answers differ, it walks each tag's rows **in file order**: the first backwards jump in local time within that ambiguous hour starts the second pass (standard time). An exact repeat that doesn't jump backwards stays in the first pass and is later counted as a duplicate, not as a fake extra hour. The report includes `dst.ambiguous_first_pass` and `ambiguous_second_pass`.
* Timestamps that already carry an offset (`-04:00`, `Z`), and tz-aware Parquet columns, are converted directly.
* **Assumption:** each tag's rows are in ascending time order in the file, which is how PI and IP.21 write them. Tags can be interleaved.

In the test file, a 10-second tag that runs through the fall-back hour comes out as an unbroken UTC series from 04:50:00 to 07:10:00. The only gaps are the 20-second steps where planted bad rows were removed.

### Totalizers

The rate is computed as change in counter over change in time, stamped at the **end** of each interval, converted from (volume unit) per hour to the target flow unit. For each interval:
* time gap greater than `max_gap_s` (default 300) → no rate
* the counter drops from at least 90% of `rollover_max` to at most 10% of it → **rollover**: add `rollover_max` to the change
* any other drop → **reset**: no rate for that interval
* the rate's quality is the worse of the two end points

Rollovers and resets appear in `report.totalizer_events` with timestamps. In the fixture, a 250 gpm totalizer that rolls over, gets reset, and runs through the DST change comes out at 250.000 gpm ± 0.0004 on every interval.

### Performance: one year of 100 tags at 10 seconds is 315,360,000 values

`import_large_file()` processes the file in two passes:

1. Read 2M rows at a time and run stage A. Rejected values are only counted. Valid values are written to disk in one folder per tag.
2. For each tag (one tag-year is 3.15M rows, which fits easily in memory), run stage B and write `out/values/<tag>.parquet`, then write `import_report.json`.

Peak memory is the larger of one chunk and one tag's data, not the size of the file.

Measured with `scripts/benchmark.py --days 3` (100 tags, crossing the fall-back day, 2.6M values) on a **2-vCPU** cloud VM: **about 212,000 values per second, so the full year extrapolates to about 25 minutes**, against a 60-minute target. Run `--days 365` on the target hardware to confirm. That needs about 15 GB of disk for the CSV.

The in-memory path (`import_historian_export`) and the large-file path share the same stage functions. A test checks that both give identical counts and values on the fixture.

---

## Milestone 2: implementation details

### Clamp-on import (`clampon.py`)

* `ClampOnLayout` sets the column names for each channel's flow and signal quality, the separator, the decimal mark, how many metadata lines to skip, the timestamp format, and the time zone.
* **Clock correction:** true time = meter time - `clock_offset_s` (a positive offset means the meter clock runs fast). Measure the offset on site against a synced clock when the meter is installed.
* **Grid alignment:** each sample is snapped to the nearest 10-second historian grid point (ties round up, so each bucket covers t-5 s to t+5 s). For each grid point, flow is the **median** (robust to spikes) and signal quality is the **minimum** (a point is only as trustworthy as its worst sample).
* The report gives row counts. Every row is either used or rejected (unparseable timestamp, nonexistent local time, duplicate timestamp), and non-numeric cells are counted per channel.

### State join (`states.py`)

Pump and valve tags are step signals, so each grid point takes the last state sample at or before it (an as-of join), with two safeguards:
* if that sample is older than `max_state_age` (default 15 min), the state is **unknown** and the point isn't judged.
* for `settling_time` (default 120 s) after any state change, the point is **in transition** and isn't judged, because the valve is still stroking and the flow is still decaying.

### Leak-by rule (`leakby.py`)

```
suspicious(t) = (valve CLOSED and not in transition  OR  pump OFF and not in transition)
                AND channel signal quality >= min_signal_quality
                AND channel flow > meter low-flow cutoff
event         = suspicious points joined into runs (gaps <= max_gap) that last >= min_duration
```

| status | when |
|---|---|
| `FLAGGED` | at least one event. Each event has start and end (UTC), duration, condition, mean and peak flow, upstream mean, minimum signal quality and a plain-English reason |
| `CLEAR` | some time was evaluable, and flow stayed at or below the cutoff (or only in bursts shorter than `min_duration`) |
| `INCONCLUSIVE` | the inputs exist, but the valve never closed and the pump never stopped during the window with good signal |
| `SKIPPED` | a required input is missing. The reasons say exactly which one (see below) |

Example reason (from the fixture):

> Downstream flow averaged 4.0 gpm (peak 4.2 gpm), above the meter's low-flow cutoff of 1 gpm, for 18.0 minutes from 2026-11-10 15:12:00 to 2026-11-10 15:29:50 UTC while valve FV-101 reported CLOSED. Signal quality stayed at or above 80. Upstream channel averaged 4.0 gpm. Flow past a closed valve suggests the valve is leaking by.

**Skip reasons:** the historian import blocked scoring (unmapped tags); no valve or pump tag configured; a configured tag missing from the historian data; a state tag with no samples near the clamp-on window; no flow, or no signal quality, on the chosen channel. Periods with poor signal or stale state are listed as minutes that were not judged.

`result.timeline` keeps the per-grid-point inputs and decisions for plotting and review, and `result.summary` gives the minutes spent in each state.

---

## Synthetic fixtures (`tests/fixtures/generate.py`, seed 42)

| file | what's planted |
|---|---|
| `historian_long.csv` (5,179 values) | Fall-back day for 6 tags with tags interleaved. Spring-forward segment plus 3 rows inside the missing hour. A totalizer that rolls over at 1,000,000 and is reset once. 2 unparseable timestamps, 3 unmapped values, 2 empty values, 2 PI digital states, 2 non-numeric values, 2 bad quality flags (text and OPC code 0), 1 unknown valve state, 3 exact duplicates (one inside the repeated hour), 1 conflicting pair, 1 Suspect value |
| `historian_wide.csv` (3,368 cells) | Per-tag quality column, an unmapped column, 3 blank cells, a digital state, a fully duplicated row |
| `leakby_historian.csv` + `clampon_export.csv` | A 1-hour scenario: valve leak-by, poor-signal period, pump off with flow below cutoff, pump off with flow above cutoff. Meter clock 45 s fast, 3 metadata lines, 2 garbage rows, 1 `----` cell |
| `expected.json` | The exact counts and events the tests assert against |

## Open questions for the client

1. Should blank cells in wide exports count as values (rejected as `empty_value`, the default) or be ignored (`wide_blank_cells="ignore"`)?
2. Should conflicting duplicates reject every copy (current), or keep the first or last copy?
3. Should uncertain quality be accepted and flagged (current), or rejected?
4. Should totalizer rates be stamped at the end of the interval (current) or the midpoint?
5. What are the leak-by thresholds: `min_duration`, `settling_time`, `max_state_age`, `min_signal_quality`? Should they come from the mapping, per valve?
6. Is the valve state a limit switch (preferred) or a commanded position?
7. Will spring-forward gap times ever really appear in exports? They're currently rejected, never shifted.
