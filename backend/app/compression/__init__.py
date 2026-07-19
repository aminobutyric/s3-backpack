"""Content-aware upload compression."""

from dataclasses import dataclass
from pathlib import PurePosixPath

from PIL import UnidentifiedImageError

from app.compression.images import compress_image
from app.compression.skiplist import should_skip
from app.compression.text import compress_text

IMAGE_EXTENSIONS = frozenset({".bmp", ".png", ".tif", ".tiff"})
TEXT_EXTENSIONS = frozenset(
    {
        ".conf",
        ".csv",
        ".ini",
        ".json",
        ".log",
        ".md",
        ".rst",
        ".sql",
        ".toml",
        ".tsv",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)


@dataclass(frozen=True)
class CompressionResult:
    key: str
    data: bytes
    content_type: str
    original_key: str
    original_size: int
    compression: str | None = None

    @property
    def stored_size(self) -> int:
        return len(self.data)

    @property
    def saved_bytes(self) -> int:
        return self.original_size - self.stored_size


def compress_upload(
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> CompressionResult:
    """Compress a supported upload when doing so makes the object smaller."""
    original = CompressionResult(
        key=key,
        data=data,
        content_type=content_type,
        original_key=key,
        original_size=len(data),
    )
    if not data or should_skip(key):
        return original

    extension = PurePosixPath(key.lower()).suffix

    if _is_image(extension, content_type):
        try:
            compressed = compress_image(data)
        except (UnidentifiedImageError, OSError, ValueError):
            return original
        if len(compressed) >= len(data):
            return original
        return CompressionResult(
            key=str(PurePosixPath(key).with_suffix(".webp")),
            data=compressed,
            content_type="image/webp",
            original_key=key,
            original_size=len(data),
            compression="webp",
        )

    if _is_text(extension, content_type):
        compressed = compress_text(data)
        if len(compressed) >= len(data):
            return original
        return CompressionResult(
            key=f"{key}.zst",
            data=compressed,
            content_type="application/zstd",
            original_key=key,
            original_size=len(data),
            compression="zstd",
        )

    return original


def _is_image(extension: str, content_type: str) -> bool:
    return extension in IMAGE_EXTENSIONS or content_type.lower() in {
        "image/bmp",
        "image/png",
        "image/tiff",
    }


def _is_text(extension: str, content_type: str) -> bool:
    normalized_content_type = content_type.lower().split(";", maxsplit=1)[0].strip()
    return (
        extension in TEXT_EXTENSIONS
        or normalized_content_type.startswith("text/")
        or normalized_content_type
        in {
            "application/json",
            "application/sql",
            "application/toml",
            "application/xml",
            "application/x-yaml",
        }
    )
