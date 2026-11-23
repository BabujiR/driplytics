"""Command line.

python -m driplytics_engine import EXPORT.csv --mapping tags.csv \\
    [--tz America/New_York] [--out out/] [--large]
python -m driplytics_engine leakby HIST.csv CLAMP.csv --mapping tags.csv \\
    --valve fv101_closed --pump pump_201_running \\
    --cutoff 1.0 [--clock-offset 45] [--clampon-layout layout.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .clampon import ClampOnLayout, load_clampon_export
from .importer import ImportConfig, import_historian_export, import_large_file
from .leakby import LeakByConfig, run_leak_by_check
from .mapping import TagMapping
from .readers import ExportLayout


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="driplytics_engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("import", help="import a historian export")
    i.add_argument("export")
    i.add_argument("--mapping", required=True)
    i.add_argument("--tz", default="America/New_York")
    i.add_argument("--out", default="out")
    i.add_argument("--format", choices=["auto", "long", "wide"], default="auto")
    i.add_argument("--timestamp-format")
    i.add_argument("--quality-suffix")
    i.add_argument("--large", action="store_true", help="chunked mode for very large files")

    lb = sub.add_parser("leakby", help="clamp-on import + valve leak-by check")
    lb.add_argument("historian")
    lb.add_argument("clampon")
    lb.add_argument("--mapping", required=True)
    lb.add_argument("--tz", default="America/New_York")
    lb.add_argument("--valve")
    lb.add_argument("--pump")
    lb.add_argument("--cutoff", type=float, required=True)
    lb.add_argument("--unit", default="gpm")
    lb.add_argument("--min-sq", type=float, default=60)
    lb.add_argument("--clock-offset", type=float, default=0.0)
    lb.add_argument(
        "--clampon-layout", help="JSON file with ClampOnLayout fields (column names, skiprows, ...)"
    )
    lb.add_argument("--channel", choices=["downstream", "upstream"], default="downstream")

    a = p.parse_args(argv)
    mapping = TagMapping.from_csv(a.mapping)
    cfg = ImportConfig(timezone=a.tz, keep_ledger=False)

    if a.cmd == "import":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        lay = ExportLayout(
            format=a.format, timestamp_format=a.timestamp_format, quality_suffix=a.quality_suffix
        )
        if a.large:
            res = import_large_file(a.export, mapping, out, lay, cfg)
        else:
            res = import_historian_export(a.export, mapping, lay, cfg)
            try:
                res.values.to_parquet(out / "values.parquet", index=False)
            except ImportError:
                res.values.to_csv(out / "values.csv", index=False)
            res.report.to_json(out / "import_report.json")
        print(res.report.summary())
        return 0 if res.report.scoring_allowed else 2

    hist = import_historian_export(a.historian, mapping, config=cfg)
    lay = json.loads(Path(a.clampon_layout).read_text()) if a.clampon_layout else {}
    clamp = load_clampon_export(
        a.clampon,
        ClampOnLayout(**{"timezone": a.tz, "flow_unit": a.unit, **lay}),
        clock_offset_s=a.clock_offset,
    )
    r = run_leak_by_check(
        clamp,
        hist.values,
        LeakByConfig(
            valve_state_tag=a.valve,
            pump_state_tag=a.pump,
            low_flow_cutoff=a.cutoff,
            flow_unit=a.unit,
            min_signal_quality=a.min_sq,
            flow_channel=a.channel,
        ),
        hist.report,
    )
    print(json.dumps({"status": r.status, "reasons": r.reasons, "summary": r.summary}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
