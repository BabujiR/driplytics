"""Paths that may be local files or object-storage URLs (ADR 0005, ADR 0007).

Every engine entry point accepts either a local path (``C:\\data\\export.csv``, ``/tmp/x.csv``)
or an fsspec URL (``s3://bucket/key``, ``gs://bucket/key``, ``memory://key``). URLs need the
matching fsspec backend installed (s3fs for s3://, gcsfs for gs://) and accept backend
options through ``storage_options`` (credentials, ``client_kwargs={"endpoint_url": ...}``).
"""

from __future__ import annotations

import os
import posixpath
from pathlib import Path
from typing import IO, Any

PathLike = str | Path
StorageOptions = dict[str, Any] | None


def is_url(path: PathLike) -> bool:
    """True for fsspec URLs such as s3://, gs:// and memory://. Windows drive letters are not URLs."""
    return isinstance(path, str) and "://" in path


def join(base: PathLike, *parts: str) -> PathLike:
    if is_url(base):
        return posixpath.join(str(base).rstrip("/"), *parts)
    return Path(base, *parts)


def suffix(path: PathLike) -> str:
    name = str(path).replace("\\", "/").rsplit("/", 1)[-1]
    return os.path.splitext(name)[1].lower()


def _fs(path: str, storage_options: StorageOptions) -> tuple[Any, str]:
    import fsspec

    return fsspec.core.url_to_fs(path, **(storage_options or {}))


def makedirs(path: PathLike, storage_options: StorageOptions = None) -> None:
    if is_url(path):
        fs, p = _fs(str(path), storage_options)
        fs.makedirs(p, exist_ok=True)
    else:
        Path(path).mkdir(parents=True, exist_ok=True)


def open_file(path: PathLike, mode: str = "rb", storage_options: StorageOptions = None) -> IO[Any]:
    """Open a local file or URL. Use as a context manager."""
    if is_url(path):
        import fsspec

        return fsspec.open(str(path), mode, **(storage_options or {})).open()  # type: ignore[no-any-return]
    return open(path, mode, encoding=None if "b" in mode else "utf-8")


def size(path: PathLike, storage_options: StorageOptions = None) -> int | None:
    """Size in bytes, or None if it can't be determined."""
    try:
        if is_url(path):
            fs, p = _fs(str(path), storage_options)
            return int(fs.size(p))
        return os.path.getsize(path)
    except Exception:
        return None


def write_text(path: PathLike, text: str, storage_options: StorageOptions = None) -> None:
    with open_file(path, "w", storage_options) as fh:
        fh.write(text)


def pandas_path(path: PathLike) -> str | Path:
    """Value to hand to pandas read_*/to_* functions (they understand URLs natively)."""
    return str(path) if is_url(path) else Path(path)


def pandas_storage_options(path: PathLike, storage_options: StorageOptions) -> StorageOptions:
    """pandas rejects storage_options for local paths, so only pass them for URLs."""
    return storage_options if is_url(path) else None
