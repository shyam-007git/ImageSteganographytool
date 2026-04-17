import hashlib
from PIL import Image


def compute_image_hash(image_path: str) -> str:
    """Compute SHA-256 hash of raw pixel data of an image."""
    image = Image.open(image_path).convert("RGB")
    img_bytes = image.tobytes()
    return hashlib.sha256(img_bytes).hexdigest()


def verify_integrity(stored_hash: str, image_path: str) -> bool:
    """
    Recompute the hash of the image and compare to stored_hash.
    Returns True if image is unmodified, False if tampered.
    """
    current_hash = compute_image_hash(image_path)
    return current_hash == stored_hash