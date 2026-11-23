"""Throughput benchmark for the 'one year, 100 tags, 10 s' requirement.

    python scripts/benchmark.py --days 3            # quick: 100 tags x 3 days  = 2.6M values
    python scripts/benchmark.py --days 365          # the real target: 315,360,000 values (~15 GB CSV)

Writes a synthetic long-format CSV (local time, so DST is included when the range
crosses it), runs import_large_file(), and extrapolates to the full-year target.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from plant_ingest import TagMapping, import_large_file  # noqa: E402

TARGET_VALUES = 365 * 8640 * 100


def make_inputs(work: Path, days: int, tags: int, start: str) -> tuple[Path, Path]:
    names = [f"FIT-{i:03d}.PV" for i in range(tags)]
    pd.DataFrame({"raw_tag": names, "canonical_tag": [f"flow_{i:03d}" for i in range(tags)],
                  "role": "flow", "source_unit": "gpm", "target_unit": "m3/h"}).to_csv(work / "map.csv", index=False)
    csv = work / "big.csv"
    rng = np.random.default_rng(0)
    with open(csv, "w") as f:
        f.write("timestamp,tag,value,quality\n")
        for d in range(days):  # one day at a time keeps memory flat
            utc = pd.date_range(pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=d), periods=8640, freq="10s")
            local = utc.tz_convert("America/New_York").strftime("%Y-%m-%d %H:%M:%S")
            ts = np.repeat(np.asarray(local), tags)
            tg = np.tile(np.asarray(names), len(utc))
            val = np.round(rng.normal(250, 5, len(ts)), 3).astype(str)
            pd.DataFrame({"timestamp": ts, "tag": tg, "value": val, "quality": "Good"}).to_csv(
                f, header=False, index=False)
    return csv, work / "map.csv"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--tags", type=int, default=100)
    ap.add_argument("--start", default="2026-10-31")   # crosses the 2026-11-01 fall-back
    ap.add_argument("--chunksize", type=int, default=2_000_000)
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        t0 = time.perf_counter()
        csv, mp = make_inputs(work, a.days, a.tags, a.start)
        print(f"generated {csv.stat().st_size / 1e6:,.0f} MB in {time.perf_counter() - t0:,.1f} s")
        t0 = time.perf_counter()
        res = import_large_file(csv, TagMapping.from_csv(mp), work / "out", chunksize=a.chunksize)
        el = time.perf_counter() - t0
        r = res.report
        rate = r.total_values / el
        print(r.summary())
        print(f"imported {r.total_values:,} values in {el:,.1f} s -> {rate:,.0f} values/s")
        print(f"DST: {r.dst}")
        print(f"extrapolated full year (100 tags x 10 s = {TARGET_VALUES:,} values): "
              f"{TARGET_VALUES / rate / 60:,.1f} min (target < 60 min)")


if __name__ == "__main__":
    main()
