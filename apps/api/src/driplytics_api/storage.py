"""Object storage for the API: upload URLs and existence checks (ADR 0005, 0007, 0017).

Upload URLs are S3-style presigned PUTs. They work with MinIO (local), AWS S3 and Google Cloud
Storage through its S3-interoperable XML API (endpoint https://storage.googleapis.com + HMAC keys),
so the browser uploads straight to the bucket and large files never pass through the API.
"""

from pathlib import Path
from typing import Any

import fsspec

from .settings import Settings


def presign_put(settings: Settings, bucket: str, key: str) -> dict[str, Any]:
    """Return {url, method, headers, expires_in} for a direct browser upload."""
    if settings.storage_protocol == "file":  # tests and offline dev: "upload" by writing the file path
        return {
            "url": settings.object_url(bucket, key),
            "method": "PUT",
            "headers": {},
            "expires_in": settings.upload_url_expiry_s,
        }
    import botocore.session
    from botocore.config import Config

    client = botocore.session.get_session().create_client(
        "s3",
        endpoint_url=settings.storage_public_endpoint_url or settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_key,
        aws_secret_access_key=settings.storage_secret,
        region_name=settings.storage_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    url = client.generate_presigned_url(
        "put_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=settings.upload_url_expiry_s
    )
    return {"url": str(url), "method": "PUT", "headers": {}, "expires_in": settings.upload_url_expiry_s}


def object_size(settings: Settings, bucket: str, key: str) -> int | None:
    """Size in bytes if the object exists, else None."""
    url = settings.object_url(bucket, key)
    if settings.storage_protocol == "file":
        p = Path(url)
        return p.stat().st_size if p.is_file() else None
    fs, path = fsspec.core.url_to_fs(url, **(settings.storage_options() or {}))
    try:
        fs.invalidate_cache()
        if not fs.exists(path):
            return None
        return int(fs.size(path))
    except FileNotFoundError:
        return None
