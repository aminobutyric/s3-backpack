from io import BytesIO

import zstandard
from PIL import Image

from app.compression import compress_upload
from app.compression.skiplist import should_skip


def test_skiplist_is_case_insensitive() -> None:
    assert should_skip("archives/database.ZIP")
    assert should_skip("photos/portrait.JPG")
    assert should_skip("exports/events.json.zst")
    assert not should_skip("photos/screenshot.png")
    assert not should_skip("logs/service.log")


def test_repetitive_text_is_compressed_with_zstd() -> None:
    original = (b"garage request completed\n" * 500)

    result = compress_upload("logs/garage.log", original, "text/plain")

    assert result.key == "logs/garage.log.zst"
    assert result.content_type == "application/zstd"
    assert result.compression == "zstd"
    assert result.stored_size < result.original_size
    assert result.saved_bytes == result.original_size - result.stored_size
    assert zstandard.ZstdDecompressor().decompress(result.data) == original


def test_compression_is_skipped_when_zstd_would_make_text_larger() -> None:
    original = b"small"

    result = compress_upload("note.txt", original, "text/plain")

    assert result.key == "note.txt"
    assert result.data == original
    assert result.compression is None
    assert result.saved_bytes == 0


def test_png_is_converted_to_smaller_webp() -> None:
    original = _make_bmp_image()

    result = compress_upload("photos/sample.bmp", original, "image/bmp")

    assert result.key == "photos/sample.webp"
    assert result.content_type == "image/webp"
    assert result.compression == "webp"
    assert result.stored_size < result.original_size

    with Image.open(BytesIO(result.data)) as converted:
        assert converted.format == "WEBP"
        assert converted.size == (128, 128)


def test_invalid_image_data_is_stored_unchanged() -> None:
    original = b"this is not an image"

    result = compress_upload("photos/broken.png", original, "image/png")

    assert result.key == "photos/broken.png"
    assert result.data == original
    assert result.compression is None


def test_already_compressed_file_is_stored_unchanged() -> None:
    original = b"pretend this is a zip archive"

    result = compress_upload("backup.zip", original, "application/zip")

    assert result.key == "backup.zip"
    assert result.data == original
    assert result.compression is None


def _make_bmp_image() -> bytes:
    pixels = bytes((index * 37 + index // 17) % 256 for index in range(128 * 128 * 3))
    image = Image.frombytes("RGB", (128, 128), pixels)
    output = BytesIO()
    image.save(output, format="BMP")
    return output.getvalue()
