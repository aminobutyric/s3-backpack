from dataclasses import dataclass
from urllib.parse import quote, unquote

COMPRESSION_KEY = "s3gw-compression"
ORIGINAL_KEY = "s3gw-original-key"
ORIGINAL_CONTENT_TYPE_KEY = "s3gw-original-content-type"
ORIGINAL_SIZE_KEY = "s3gw-original-size"


@dataclass(frozen=True)
class CompressionMetadata:
    method: str
    original_key: str
    original_content_type: str
    original_size: int


def build_compression_metadata(
    method: str,
    original_key: str,
    original_content_type: str,
    original_size: int,
) -> dict[str, str]:
    return {
        COMPRESSION_KEY: method,
        ORIGINAL_KEY: quote(original_key, safe=""),
        ORIGINAL_CONTENT_TYPE_KEY: original_content_type,
        ORIGINAL_SIZE_KEY: str(original_size),
    }


def parse_compression_metadata(
    metadata: dict[str, str],
) -> CompressionMetadata | None:
    try:
        method = metadata[COMPRESSION_KEY]
        original_key = unquote(metadata[ORIGINAL_KEY])
        original_content_type = metadata[ORIGINAL_CONTENT_TYPE_KEY]
        original_size = int(metadata[ORIGINAL_SIZE_KEY])
    except (KeyError, TypeError, ValueError):
        return None

    if method not in {"zstd", "webp"} or not original_key or original_size < 0:
        return None
    return CompressionMetadata(
        method=method,
        original_key=original_key,
        original_content_type=original_content_type or "application/octet-stream",
        original_size=original_size,
    )
