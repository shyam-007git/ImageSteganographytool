from PIL import Image


def get_capacity(image_path: str) -> int:
    """Returns max number of characters the image can hold."""
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    total_pixels = width * height
    # Each pixel holds 3 bits (1 per RGB channel), 8 bits = 1 char
    max_bytes = (total_pixels * 3) // 8
    # Reserve 100 bytes for salt (16) + hash (64) + padding
    max_chars = max_bytes - 100
    return max(0, max_chars)


def get_usage(message: str, image_path: str):
    """
    Returns (used_chars, max_chars, percent_used).
    percent_used is a float 0.0 - 100.0
    """
    capacity = get_capacity(image_path)
    used = len(message.encode("utf-8"))
    if capacity == 0:
        return used, 0, 100.0
    percent = min((used / capacity) * 100, 100.0)
    return used, capacity, round(percent, 2)