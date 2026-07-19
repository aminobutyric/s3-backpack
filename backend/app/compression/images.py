"""Image conversion to WebP."""

from io import BytesIO

from PIL import Image, ImageOps

WEBP_QUALITY = 85


def compress_image(data: bytes) -> bytes:
    """Convert image bytes to WebP while preserving dimensions and alpha."""
    with Image.open(BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source)
        image.load()

        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")

        output = BytesIO()
        image.save(output, format="WEBP", quality=WEBP_QUALITY, method=4)
        return output.getvalue()
