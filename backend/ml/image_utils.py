"""Image helpers shared by upload ingest and face detection.

Phones store portrait shots sideways plus an EXIF Orientation tag. Browsers honour
the tag, PIL does not, so every pixel coordinate we store (face boxes, width/height)
has to be computed on the *oriented* image to line up with what the user sees.
"""
from datetime import datetime, timezone

from PIL import Image, ImageOps

EXIF_IFD_POINTER = 0x8769
DATETIME_ORIGINAL = 0x9003
DATETIME_DIGITIZED = 0x9004
DATETIME = 0x0132


def open_oriented(source):
    """Open an image path/file as an RGB image with EXIF orientation applied."""
    with Image.open(source) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def crop_face(image, box):
    """Crop a detected face exactly as the upload view stores it.

    box is [x, y, width, height]. A negative origin is clamped to the image edge
    (width and height are kept). Returns (x, y, crop) with the clamped origin.
    """
    x, y, width, height = box
    x, y = max(0, x), max(0, y)
    return x, y, image.crop((x, y, x + width, y + height))


def read_taken_at(image):
    """Capture time from EXIF, or None.

    EXIF stores camera wall-clock time with no timezone. It is labelled UTC here
    so the calendar day a photo was taken survives storage unchanged.
    """
    try:
        exif = image.getexif()
        raw = (
            exif.get_ifd(EXIF_IFD_POINTER).get(DATETIME_ORIGINAL)
            or exif.get_ifd(EXIF_IFD_POINTER).get(DATETIME_DIGITIZED)
            or exif.get(DATETIME)
        )
        if isinstance(raw, bytes):
            raw = raw.decode("ascii", errors="ignore")
        return datetime.strptime(raw.strip("\x00 "), "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        # EXIF comes from untrusted files: missing, truncated and zeroed dates
        # ("0000:00:00 00:00:00") are all common, and none should fail an upload.
        return None
