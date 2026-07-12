from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_IMAGE_EDGE = 2560
WEBP_QUALITY = 82


def normalize_editor_image(uploaded_file):
    """Correct orientation, resize, strip metadata, and encode a UUID-named WebP."""
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as source:
        source.verify()
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
        if image.mode in {"RGBA", "LA"}:
            normalized = image.convert("RGBA")
        else:
            normalized = image.convert("RGB")
        output = BytesIO()
        normalized.save(output, format="WEBP", quality=WEBP_QUALITY, method=6, optimize=True)
    return ContentFile(output.getvalue(), name=f"{uuid4().hex}.webp")
