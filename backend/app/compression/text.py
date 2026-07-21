"""Lossless text compression using zstd."""

import zstandard

ZSTD_LEVEL = 3


def compress_text(data: bytes) -> bytes:
    return zstandard.ZstdCompressor(level=ZSTD_LEVEL).compress(data)


def decompress_text(data: bytes, max_output_size: int) -> bytes:
    return zstandard.ZstdDecompressor().decompress(
        data,
        max_output_size=max_output_size,
    )
