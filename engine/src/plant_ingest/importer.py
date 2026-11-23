"""Milestone 1: historian export importer.

Pipeline (every input value ends in exactly one bucket):

Stage A - row-local checks (vectorized, can run chunk by chunk):
    1. UNPARSEABLE_TIMESTAMP   2. UNMAPPED_TAG   3. EMPTY_VALUE
    4. BAD_QUALITY (quality flag Bad, or a PI digital state like "I/O Timeout" as the value)
    5. NON_NUMERIC_VALUE (analog tags)   6. UNRECOGNIZED_STATE (pump/valve tags)

Stage B - order-dependent checks, per tag (needs all of one tag's rows):
    7. NONEXISTENT_LOCAL_TIME (spring-forward gap) after local -> UTC with DST resolution
    8. Duplicates on (tag, UTC time):
         identical values  -> first ACCEPTED, the rest DUPLICATE
         different values  -> all REJECTED as CONFLICTING_DUPLICATE (we cannot know which is right)
    9. Accepted values: unit conversion; totalizers -> rates.

Two entry points share the exact same stage functions:
    import_historian_export()  whole file in memory -> DataFrame (tests, files up to a few GB)
    import_large_file()        chunked + spill-to-disk per tag -> per-tag output files
                               (1 year x 100 tags x 10 s = 315M values)
"""
from __future__ import annotations

import shutil
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .constants import CODE_REASON, REASON_CODE, Outcome, Quality, Reason
from .mapping import TagMapping
from .quality import is_digital_state, normalize_quality
from .readers import ExportLayout, RawChunk, iter_raw_chunks, read_raw
from .report import ImportReport
from .timeconv import LocalizeStats, localize_to_utc, parse_timestamps
from .totalizer import totalizer_to_rate
from .units import convert

VALUE_COLUMNS = ["timestamp_utc", "tag", "raw_tag", "value", "unit", "quality", "role", "derived"]


@dataclass
class ImportConfig:
    timezone: str = "America/New_York"          # zone of naive timestamps in the export
    blank_quality: Quality = Quality.GOOD       # quality assumed when the flag is blank/absent
    max_examples_per_reason: int = 20           # rejected rows copied into the report
    keep_ledger: bool = True                    # per-value outcome table (in-memory path only)


@dataclass
class ImportResult:
    values: pd.DataFrame | None                 # clean long DataFrame (in-memory path)
    report: ImportReport
    ledger: pd.DataFrame | None = None          # seq, raw_tag, outcome, reason for every input value


# --------------------------------------------------------------------------- helpers

def _per_category(cat: pd.Series, fn, default) -> np.ndarray:
    """Evaluate fn once per distinct tag and broadcast via category codes (fast on huge frames)."""
    cats = cat.cat.categories
    lut = np.array([fn(c) for c in cats] + [default], dtype=object)
    codes = cat.cat.codes.to_numpy()
    return lut[np.where(codes < 0, len(cats), codes)]


def _empty_values() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="float64" if c == "value" else
                                      "bool" if c == "derived" else
                                      "datetime64[us, UTC]" if c == "timestamp_utc" else "string")
                         for c in VALUE_COLUMNS})


@dataclass
class _Tally:
    """Running counts across chunks/tags; becomes the ImportReport."""
    cfg: ImportConfig
    total: int = 0
    by_code: Counter = field(default_factory=Counter)
    duplicates: int = 0
    accepted: int = 0
    accepted_uncertain: int = 0
    unmapped: Counter = field(default_factory=Counter)
    examples: dict = field(default_factory=dict)
    dst: LocalizeStats = field(default_factory=LocalizeStats)
    tot_events: list = field(default_factory=list)
    tot_gaps: int = 0
    blank_ignored: int = 0
    tags: dict = field(default_factory=dict)

    def add_examples(self, codes: np.ndarray, rows: pd.DataFrame, ts_col: str) -> None:
        k = self.cfg.max_examples_per_reason
        for c in np.unique(codes[codes > 0]):
            reason = CODE_REASON[int(c)].value
            have = self.examples.setdefault(reason, [])
            if len(have) >= k:
                continue
            sel = rows.iloc[np.flatnonzero(codes == c)[: k - len(have)]]
            for r in sel.itertuples(index=False):
                have.append({"seq": int(r.seq), "raw_tag": str(r.raw_tag),
                             "timestamp": str(getattr(r, ts_col)), "value": str(r.value)})

    def report(self, source: str, fmt: str, elapsed: float, output_path: str | None) -> ImportReport:
        rejected_by = {r.value: int(self.by_code.get(REASON_CODE[r], 0)) for r in Reason}
        blocked = []
        if self.unmapped:
            blocked.append(f"{len(self.unmapped)} unmapped tag(s): " + ", ".join(sorted(self.unmapped)))
        if self.accepted == 0:
            blocked.append("no accepted values")
        return ImportReport(
            source=source, format=fmt, timezone=self.cfg.timezone, total_values=self.total,
            accepted=self.accepted, rejected=sum(rejected_by.values()), duplicates=self.duplicates,
            rejected_by_reason=rejected_by, accepted_uncertain=self.accepted_uncertain,
            unmapped_tags=dict(self.unmapped), scoring_allowed=not blocked,
            scoring_blocked_reasons=blocked,
            dst={"ambiguous_first_pass": self.dst.ambiguous_first_pass,
                 "ambiguous_second_pass": self.dst.ambiguous_second_pass,
                 "nonexistent_local_time": self.dst.nonexistent},
            totalizer_events=self.tot_events, totalizer_gaps=self.tot_gaps,
            tags=sorted(self.tags.values(), key=lambda d: d["tag"]),
            blank_cells_ignored=self.blank_ignored, rejected_examples=self.examples,
            elapsed_s=round(elapsed, 3),
            values_per_second=round(self.total / elapsed, 1) if elapsed > 0 else 0.0,
            output_path=output_path,
        )


# --------------------------------------------------------------------------- stage A

def _stage_a(raw: pd.DataFrame, mapping: TagMapping, layout: ExportLayout, cfg: ImportConfig
             ) -> pd.DataFrame:
    """Row-local validation. Returns seq, raw_tag, local, value, quality, code (0 = still valid)."""
    n = len(raw)
    code = np.zeros(n, np.int8)

    def mark(mask, reason: Reason) -> None:
        m = np.asarray(mask, dtype=bool) & (code == 0)
        code[m] = REASON_CODE[reason]

    local = parse_timestamps(pd.Series(raw["ts"].to_numpy()), layout.timestamp_format)
    mark(local.isna().to_numpy(), Reason.UNPARSEABLE_TIMESTAMP)

    tags = pd.Series(raw["raw_tag"].to_numpy(), dtype="string").fillna("").astype("category")
    mapped = _per_category(tags, lambda t: t in mapping, False).astype(bool)
    mark(~mapped, Reason.UNMAPPED_TAG)

    v = pd.Series(raw["value"].to_numpy())
    if pd.api.types.is_numeric_dtype(v):
        text = None
        num = v.to_numpy(dtype="float64", na_value=np.nan)
        empty = np.isnan(num)
    else:
        text = v.astype("string").str.strip().fillna("")
        empty = (text == "").to_numpy()
        t2 = text.str.replace(layout.decimal, ".", regex=False) if layout.decimal != "." else text
        num = pd.to_numeric(t2, errors="coerce").to_numpy(dtype="float64", na_value=np.nan)
    mark(empty, Reason.EMPTY_VALUE)

    qraw = raw["quality"]
    qraw = None if qraw.isna().all() else pd.Series(qraw.to_numpy())
    quality = normalize_quality(qraw, n, cfg.blank_quality)
    digital = np.zeros(n, bool)
    nonnum = ~np.isfinite(num) & ~empty
    if text is not None and nonnum.any():
        idx = np.flatnonzero(nonnum)
        digital[idx] = is_digital_state(text.iloc[idx]).to_numpy()
    mark(digital | (quality == Quality.BAD.value).to_numpy(), Reason.BAD_QUALITY)

    is_state = _per_category(tags, lambda t: t in mapping and mapping[t].role.is_state, False).astype(bool)
    mark(~is_state & ~np.isfinite(num), Reason.NON_NUMERIC_VALUE)

    sidx = np.flatnonzero(is_state & (code == 0))
    if len(sidx):
        nv = num[sidx]
        isint = np.isfinite(nv) & (nv == np.round(nv))
        as_int = np.where(isint, nv, 0).astype("int64").astype(str)
        lowered = (text.iloc[sidx].str.lower().to_numpy(dtype=object) if text is not None
                   else nv.astype(str))
        norm = np.where(isint, as_int, lowered)
        stags = tags.iloc[sidx].astype(str).to_numpy()
        lut = {}
        for t in set(stags):
            spec = mapping[t]
            lut[(t, spec.state_true)] = 1.0
            lut[(t, spec.state_false)] = 0.0
        sval = np.array([lut.get(k, np.nan) for k in zip(stags, norm)], dtype="float64")
        bad = np.isnan(sval)
        code[sidx[bad]] = REASON_CODE[Reason.UNRECOGNIZED_STATE]
        num = num.copy()
        num[sidx] = sval

    return pd.DataFrame({"seq": raw["seq"].to_numpy(), "raw_tag": tags.to_numpy(),
                         "local": local.to_numpy() if not isinstance(local.dtype, pd.DatetimeTZDtype)
                         else local, "value": num, "quality": quality.to_numpy(), "code": code})


def _tally_stage_a(t: _Tally, a: pd.DataFrame, raw: pd.DataFrame) -> None:
    codes = a["code"].to_numpy()
    t.total += len(a)
    t.by_code.update(dict(zip(*np.unique(codes[codes > 0], return_counts=True))))
    um = codes == REASON_CODE[Reason.UNMAPPED_TAG]
    if um.any():
        t.unmapped.update(pd.Series(a["raw_tag"].to_numpy()[um]).astype(str).value_counts().to_dict())
    if (codes > 0).any():
        t.add_examples(codes, raw.assign(seq=a["seq"].to_numpy()), "ts")


# --------------------------------------------------------------------------- stage B

def _stage_b(valid: pd.DataFrame, mapping: TagMapping, cfg: ImportConfig, t: _Tally
             ) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """valid: stage-A-valid rows sorted by seq. Returns (code, is_duplicate, values)."""
    valid = valid.reset_index(drop=True)
    n = len(valid)
    code = np.zeros(n, np.int8)
    local = valid["local"]
    if not pd.api.types.is_datetime64_any_dtype(local):
        local = pd.to_datetime(local)
    utc, nonexistent, st = localize_to_utc(local, valid["raw_tag"], cfg.timezone)
    t.dst.add(st)
    code[nonexistent] = REASON_CODE[Reason.NONEXISTENT_LOCAL_TIME]

    is_dup = np.zeros(n, bool)
    ok = np.flatnonzero(code == 0)
    key = pd.DataFrame({"tag": valid["raw_tag"].to_numpy()[ok], "ts": utc.to_numpy()[ok],
                        "value": valid["value"].to_numpy()[ok]}, index=ok)
    dup_any = key.duplicated(["tag", "ts"], keep=False)
    if dup_any.any():
        d = key[dup_any]
        nuniq = d.groupby(["tag", "ts"], observed=True, sort=False)["value"].transform("nunique")
        conflict = d.index[(nuniq > 1).to_numpy()]
        code[conflict] = REASON_CODE[Reason.CONFLICTING_DUPLICATE]
        same = d[(nuniq == 1).to_numpy()]
        is_dup[same.index[same.duplicated(["tag", "ts"], keep="first").to_numpy()]] = True

    t.by_code.update(dict(zip(*np.unique(code[code > 0], return_counts=True))))
    t.duplicates += int(is_dup.sum())
    if (code > 0).any():
        t.add_examples(code, valid.assign(local=local), "local")

    accepted = (code == 0) & ~is_dup
    t.accepted += int(accepted.sum())
    acc = valid[accepted].assign(timestamp_utc=utc[accepted].to_numpy())
    t.accepted_uncertain += int((acc["quality"] == Quality.UNCERTAIN.value).sum())

    parts = []
    for raw_tag, g in acc.groupby("raw_tag", observed=True, sort=False):
        raw_tag = str(raw_tag)
        spec = mapping[raw_tag]
        g = g.sort_values("timestamp_utc", kind="stable")
        if spec.is_totalizer:
            rates, ev, gaps = totalizer_to_rate(g["timestamp_utc"], g["value"].to_numpy(),
                                                g["quality"], spec)
            t.tot_events.extend(ev)
            t.tot_gaps += gaps
            ts, vals, q, unit, derived = (rates["timestamp_utc"], rates["value"].to_numpy(),
                                          rates["quality"], spec.target_unit, True)
        elif spec.role.is_state:
            ts, vals, q, unit, derived = g["timestamp_utc"], g["value"].to_numpy(), g["quality"], "", False
        else:
            ts, q, derived = g["timestamp_utc"], g["quality"], False
            vals = convert(g["value"].to_numpy(), spec.source_unit, spec.target_unit)
            unit = spec.target_unit or spec.source_unit
        part = pd.DataFrame({"timestamp_utc": pd.Series(ts.to_numpy()).dt.tz_convert("UTC")
                             if len(ts) else pd.Series([], dtype="datetime64[us, UTC]"),
                             "tag": spec.canonical_tag, "raw_tag": raw_tag, "value": vals,
                             "unit": unit, "quality": pd.Series(q).astype("string").to_numpy(),
                             "role": spec.role.value, "derived": derived})
        parts.append(part)
        prev = t.tags.get(spec.canonical_tag, {"tag": spec.canonical_tag, "raw_tag": raw_tag,
                                               "role": spec.role.value, "unit": unit,
                                               "accepted_inputs": 0, "output_rows": 0,
                                               "first_utc": None, "last_utc": None})
        prev["accepted_inputs"] += len(g)
        prev["output_rows"] += len(part)
        if len(g):
            f, l = g["timestamp_utc"].iloc[0].isoformat(), g["timestamp_utc"].iloc[-1].isoformat()
            prev["first_utc"] = min(filter(None, [prev["first_utc"], f]))
            prev["last_utc"] = max(filter(None, [prev["last_utc"], l]))
        t.tags[spec.canonical_tag] = prev

    values = pd.concat(parts, ignore_index=True) if parts else _empty_values()
    return code, is_dup, values


def _finalize_values(values: pd.DataFrame) -> pd.DataFrame:
    if values.empty:
        return _empty_values()
    values = values.sort_values(["tag", "timestamp_utc"], kind="stable", ignore_index=True)
    for c in ("tag", "raw_tag", "unit", "quality", "role"):
        values[c] = values[c].astype("category")
    return values[VALUE_COLUMNS]


# --------------------------------------------------------------------------- public API

def import_frames(raw: RawChunk, mapping: TagMapping, layout: ExportLayout | None = None,
                  config: ImportConfig | None = None, source: str = "<memory>") -> ImportResult:
    """Core in-memory import of an already-read RawChunk."""
    layout, cfg = layout or ExportLayout(), config or ImportConfig()
    t0 = time.perf_counter()
    tally = _Tally(cfg, blank_ignored=raw.blank_cells_ignored)
    frame = raw.frame.sort_values("seq", kind="stable", ignore_index=True)

    a = _stage_a(frame, mapping, layout, cfg)
    _tally_stage_a(tally, a, frame)
    valid_mask = a["code"].to_numpy() == 0
    code_b, dup_b, values = _stage_b(a[valid_mask], mapping, cfg, tally)

    ledger = None
    if cfg.keep_ledger:
        codes = a["code"].to_numpy().copy()
        dup = np.zeros(len(a), bool)
        vidx = np.flatnonzero(valid_mask)
        codes[vidx] = code_b
        dup[vidx] = dup_b
        outcome = np.where(codes > 0, Outcome.REJECTED.value,
                           np.where(dup, Outcome.DUPLICATE.value, Outcome.ACCEPTED.value))
        reason_lut = np.array([""] + [CODE_REASON[i].value for i in range(1, len(Reason) + 1)], dtype=object)
        ledger = pd.DataFrame({"seq": a["seq"].to_numpy(), "raw_tag": a["raw_tag"].astype(str).to_numpy(),
                               "outcome": outcome, "reason": reason_lut[codes]})

    report = tally.report(source, raw.format, time.perf_counter() - t0, None)
    return ImportResult(_finalize_values(values), report, ledger)


def import_historian_export(path: str | Path, mapping: TagMapping | str | Path,
                            layout: ExportLayout | None = None,
                            config: ImportConfig | None = None) -> ImportResult:
    """Import a whole CSV/Parquet export in memory. Returns clean values + report (+ ledger)."""
    if not isinstance(mapping, TagMapping):
        mapping = TagMapping.from_csv(mapping)
    t0 = time.perf_counter()
    raw = read_raw(path, layout)
    res = import_frames(raw, mapping, layout, config, source=str(path))
    res.report.elapsed_s = round(time.perf_counter() - t0, 3)
    res.report.values_per_second = round(res.report.total_values / max(res.report.elapsed_s, 1e-9), 1)
    return res


# --- large files ------------------------------------------------------------

def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        return False


def _write_part(df: pd.DataFrame, stem: Path) -> Path:
    if _has_pyarrow():
        p = stem.with_suffix(".parquet")
        df.to_parquet(p, index=False)
    else:  # fallback so the pipeline still runs without pyarrow
        p = stem.with_suffix(".pkl")
        df.to_pickle(p)
    return p


def _read_part(p: Path) -> pd.DataFrame:
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_pickle(p)


def import_large_file(path: str | Path, mapping: TagMapping | str | Path, out_dir: str | Path,
                      layout: ExportLayout | None = None, config: ImportConfig | None = None,
                      chunksize: int = 2_000_000) -> ImportResult:
    """Chunked import for exports too big for memory.

    Pass 1: read `chunksize` rows at a time, run stage A, count rejects, spill the
            still-valid rows to one folder per tag.
    Pass 2: for each tag, load its rows (one tag-year = 3.15M rows at 10 s, small),
            run stage B, write <out_dir>/values/<canonical_tag>.parquet.
    Memory is bounded by max(chunk, one tag's rows), not by file size.
    """
    if not isinstance(mapping, TagMapping):
        mapping = TagMapping.from_csv(mapping)
    layout, cfg = layout or ExportLayout(), config or ImportConfig()
    out_dir = Path(out_dir)
    (out_dir / "values").mkdir(parents=True, exist_ok=True)
    spill = Path(tempfile.mkdtemp(prefix="spill_", dir=out_dir))
    t0 = time.perf_counter()
    tally = _Tally(cfg)
    fmt = "long"
    tag_ids = {t: i for i, t in enumerate(mapping.raw_tags)}
    try:
        for ci, chunk in enumerate(iter_raw_chunks(path, layout, chunksize)):
            fmt = chunk.format
            tally.blank_ignored += chunk.blank_cells_ignored
            a = _stage_a(chunk.frame, mapping, layout, cfg)
            _tally_stage_a(tally, a, chunk.frame)
            valid = a[a["code"].to_numpy() == 0].drop(columns="code")
            for raw_tag, g in valid.groupby("raw_tag", observed=True, sort=False):
                d = spill / f"tag_{tag_ids[str(raw_tag)]:05d}"
                d.mkdir(exist_ok=True)
                _write_part(g.assign(raw_tag=g["raw_tag"].astype(str)), d / f"part_{ci:06d}")

        for d in sorted(spill.iterdir()):
            g = pd.concat([_read_part(p) for p in sorted(d.iterdir())], ignore_index=True)
            g = g.sort_values("seq", kind="stable", ignore_index=True)
            _, _, values = _stage_b(g, mapping, cfg, tally)
            if len(values):
                canon = str(values["tag"].iloc[0])
                _write_part(_finalize_values(values), out_dir / "values" / canon)
    finally:
        shutil.rmtree(spill, ignore_errors=True)

    report = tally.report(str(path), fmt, time.perf_counter() - t0, str(out_dir / "values"))
    report.to_json(out_dir / "import_report.json")
    return ImportResult(None, report, None)
