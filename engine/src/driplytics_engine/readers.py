"""Read historian exports (long or wide, CSV or Parquet) into one raw long shape.

Raw long shape (one row per input VALUE, nothing parsed or dropped yet):

    seq       int64   position of the value in the file (stable ordering key)
    ts        str | datetime   timestamp exactly as exported
    raw_tag   str
    value     str | number     value exactly as exported
    quality   str | number | None

Wide files are "melted": every non-timestamp cell becomes one value. That is
why, for wide files, total_values = rows x tag columns (blank cells included
unless wide_blank_cells="ignore").
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from . import storage
from .storage import PathLike, StorageOptions


@dataclass
class ExportLayout:
    """Column layout of a historian export. Defaults match a typical PI/IP.21 long CSV."""

    format: Literal["auto", "long", "wide"] = "auto"
    timestamp_col: str = "timestamp"
    tag_col: str = "tag"
    value_col: str = "value"
    quality_col: str | None = "quality"
    # Wide only: a column named f"{tag}{quality_suffix}" holds that tag's quality.
    quality_suffix: str | None = None
    # Wide only: explicit tag columns; None = every column except timestamp/quality columns.
    tag_columns: list[str] | None = None
    timestamp_format: str | None = None  # e.g. "%m/%d/%Y %I:%M:%S %p"; None = auto
    sep: str = ","
    decimal: str = "."
    skiprows: int = 0  # metadata lines above the header
    encoding: str = "utf-8-sig"
    wide_blank_cells: Literal["reject", "ignore"] = "reject"


@dataclass
class RawChunk:
    frame: pd.DataFrame
    blank_cells_ignored: int = 0
    format: str = "long"
    rows: int = 0  # input file rows in this chunk (wide files melt one row into many values)


def _is_parquet(path: PathLike) -> bool:
    return storage.suffix(path) in (".parquet", ".pq")


def _detect_format(columns: list[str], layout: ExportLayout) -> str:
    if layout.format != "auto":
        return layout.format
    cols = {c.strip() for c in columns}
    return "long" if {layout.tag_col, layout.value_col} <= cols else "wide"


def _iter_frames(
    path: PathLike, layout: ExportLayout, chunksize: int | None, storage_options: StorageOptions = None
) -> Iterator[pd.DataFrame]:
    if _is_parquet(path):
        try:
            import pyarrow.parquet as pq
        except ImportError as e:  # pragma: no cover - depends on environment
            raise ImportError("Reading Parquet requires pyarrow (pip install pyarrow)") from e
        with storage.open_file(path, "rb", storage_options) as fh:
            pf = pq.ParquetFile(fh)
            for batch in pf.iter_batches(batch_size=chunksize or 1_000_000):
                yield batch.to_pandas()
        return
    # Read everything as text: we decide what is a number, a blank or a digital state.
    kw = dict(
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        sep=layout.sep,
        skiprows=layout.skiprows,
        encoding=layout.encoding,
        skipinitialspace=True,
        storage_options=storage.pandas_storage_options(path, storage_options),
    )
    src = storage.pandas_path(path)
    if chunksize:
        yield from pd.read_csv(src, chunksize=chunksize, **kw)
    else:
        yield pd.read_csv(src, **kw)


def estimate_input_rows(
    path: PathLike, layout: ExportLayout | None = None, storage_options: StorageOptions = None
) -> int | None:
    """Rough number of data rows, for progress reporting only. Exact for Parquet, sampled for CSV."""
    layout = layout or ExportLayout()
    try:
        if _is_parquet(path):
            import pyarrow.parquet as pq

            with storage.open_file(path, "rb", storage_options) as fh:
                return int(pq.ParquetFile(fh).metadata.num_rows)
        total = storage.size(path, storage_options)
        if not total:
            return None
        with storage.open_file(path, "rb", storage_options) as fh:
            sample = fh.read(256 * 1024)
        lines = sample.count(b"\n")
        if lines == 0:
            return 1
        if len(sample) >= total:  # whole file sampled: exact
            return max(lines - 1 - layout.skiprows, 0)
        return max(int(total / (len(sample) / lines)) - 1 - layout.skiprows, 0)
    except Exception:
        return None


def _to_long(df: pd.DataFrame, layout: ExportLayout, seq_start: int) -> pd.DataFrame:
    df = df.rename(columns=lambda c: str(c).strip())
    for c in (layout.timestamp_col, layout.tag_col, layout.value_col):
        if c not in df.columns:
            raise ValueError(f"long-format export is missing column '{c}' (found {list(df.columns)})")
    q = layout.quality_col if layout.quality_col in df.columns else None
    n = len(df)
    return pd.DataFrame(
        {
            "seq": pd.RangeIndex(seq_start, seq_start + n).to_numpy(),
            "ts": df[layout.timestamp_col].to_numpy(),
            "raw_tag": df[layout.tag_col].astype("string").str.strip().to_numpy(),
            "value": df[layout.value_col].to_numpy(),
            "quality": df[q].to_numpy() if q else None,
        }
    )


def _wide_to_long(df: pd.DataFrame, layout: ExportLayout, row_start: int) -> tuple[pd.DataFrame, int]:
    df = df.rename(columns=lambda c: str(c).strip())
    if layout.timestamp_col not in df.columns:
        raise ValueError(f"wide-format export is missing column '{layout.timestamp_col}'")
    sfx = layout.quality_suffix
    if layout.tag_columns is not None:
        tags = list(layout.tag_columns)
    else:
        tags = [c for c in df.columns if c != layout.timestamp_col and not (sfx and c.endswith(sfx))]
    n, k = len(df), len(tags)
    parts = []
    for j, tag in enumerate(tags):
        qcol = f"{tag}{sfx}" if sfx and f"{tag}{sfx}" in df.columns else None
        parts.append(
            pd.DataFrame(
                {
                    # seq follows file order: row-major, then column order
                    "seq": (pd.RangeIndex(row_start, row_start + n).to_numpy() * k + j),
                    "ts": df[layout.timestamp_col].to_numpy(),
                    "raw_tag": tag,
                    "value": df[tag].to_numpy(),
                    "quality": df[qcol].to_numpy() if qcol else None,
                }
            )
        )
    out = (
        pd.concat(parts, ignore_index=True)
        if parts
        else pd.DataFrame(columns=["seq", "ts", "raw_tag", "value", "quality"])
    )
    out = out.sort_values("seq", kind="stable", ignore_index=True)
    ignored = 0
    if layout.wide_blank_cells == "ignore":
        blank = out["value"].isna() | (out["value"].astype("string").str.strip() == "")
        ignored = int(blank.sum())
        out = out[~blank.to_numpy()].reset_index(drop=True)
    return out, ignored


def iter_raw_chunks(
    path: PathLike,
    layout: ExportLayout | None = None,
    chunksize: int | None = None,
    storage_options: StorageOptions = None,
) -> Iterator[RawChunk]:
    """Yield RawChunk objects in file order. chunksize = input ROWS per chunk (None = whole file).

    `path` is a local path or an fsspec URL (s3://, gs://, memory://), see storage.py.
    """
    layout = layout or ExportLayout()
    fmt = None
    row_pos = 0
    for df in _iter_frames(path, layout, chunksize, storage_options):
        fmt = fmt or _detect_format(list(df.columns), layout)
        if fmt == "long":
            yield RawChunk(_to_long(df, layout, row_pos), 0, fmt, len(df))
        else:
            frame, ignored = _wide_to_long(df, layout, row_pos)
            yield RawChunk(frame, ignored, fmt, len(df))
        row_pos += len(df)


def read_raw(
    path: PathLike, layout: ExportLayout | None = None, storage_options: StorageOptions = None
) -> RawChunk:
    """Whole file as a single RawChunk."""
    chunks = list(iter_raw_chunks(path, layout, None, storage_options))
    if len(chunks) == 1:
        return chunks[0]
    return RawChunk(
        pd.concat([c.frame for c in chunks], ignore_index=True),
        sum(c.blank_cells_ignored for c in chunks),
        chunks[0].format if chunks else "long",
        sum(c.rows for c in chunks),
    )
