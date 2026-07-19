"""File types that should not be compressed again."""

from pathlib import PurePosixPath

# These formats are already compressed, or converting them would be surprising
# or destructive (for example, dropping animation from a GIF).
SKIP_EXTENSIONS = frozenset(
    {
        ".7z",
        ".avi",
        ".bz2",
        ".flac",
        ".gif",
        ".gz",
        ".jpeg",
        ".jpg",
        ".m4a",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".ogg",
        ".pdf",
        ".rar",
        ".webm",
        ".webp",
        ".xz",
        ".zip",
        ".zst",
    }
)


def should_skip(key: str) -> bool:
    """Return whether the object's final extension is on the skip-list."""
    return PurePosixPath(key.lower()).suffix in SKIP_EXTENSIONS
