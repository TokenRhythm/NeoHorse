"""Bounded inline image decoding. Never fetch URLs or open caller-supplied paths."""
import base64
import binascii
from io import BytesIO
import warnings

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_PIXELS = 4 * 1024 * 1024
MIME_FORMAT = {'image/png': 'PNG', 'image/jpeg': 'JPEG', 'image/webp': 'WEBP'}

def decode_image(value):
    from PIL import Image, UnidentifiedImageError
    if not isinstance(value, str) or not value.startswith('data:') or ',' not in value:
        raise ValueError('image must be a data:image/png|jpeg|webp;base64,... string; URLs and paths are not supported')
    header, encoded = value.split(',', 1)
    mime = header[5:].removesuffix(';base64')
    if header != 'data:' + mime + ';base64' or mime not in MIME_FORMAT:
        raise ValueError('image supports only base64 PNG, JPEG or WebP data URLs')
    if len(encoded) > 4 * ((MAX_IMAGE_BYTES + 2) // 3):
        raise ValueError('Encoded image exceeds 4 MiB decoded-byte limit')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('Invalid image base64') from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image must contain 1 byte to 4 MiB')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format != MIME_FORMAT[mime]:
                    raise ValueError('Image MIME type does not match decoded format')
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('Image exceeds 4 megapixels')
                if getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('Animated/multi-frame images are not supported')
                source.load()
                return source.convert('RGB')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError('Invalid, truncated or oversized image') from exc
