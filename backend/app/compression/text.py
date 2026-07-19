"""Lossless text compression using zstd."""

import zstandard

ZSTD_LEVEL = 3


def compress_text(data: bytes) -> bytes:
    return zstandard.ZstdCompressor(level=ZSTD_LEVEL).compress(data)
