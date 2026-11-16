"""Validate encoded images before invoking native OCR libraries."""
import io
import warnings
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException

MAX_PIXELS = 16_000_000
FORMATS = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}


def validate_image(filename, content):
    suffix = Path(filename).suffix.lower()
    if suffix not in FORMATS:
        raise HTTPException(415, 'Upload a JPEG, PNG or WebP image.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.width * image.height > MAX_PIXELS or image.n_frames != 1:
                    raise HTTPException(413, 'Use a single image with at most 16 million pixels.')
                if image.format != FORMATS[suffix]:
                    raise HTTPException(415, 'Image contents do not match the file extension.')
                image.verify()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise HTTPException(413, 'Image dimensions are too large.') from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise HTTPException(415, 'The uploaded file is not a valid image.') from error
    return suffix
