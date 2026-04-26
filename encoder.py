import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image

from integrity import compute_image_hash


def derive_key_from_password(password: str, salt: bytes = None):
    """
    Derive a Fernet-compatible key from a plain-text password.
    Returns (key_bytes, salt_bytes).
    """
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key, salt


def _text_to_bits(text: str) -> str:
    """Convert a string to a binary string."""
    return "".join(format(byte, "08b") for byte in text.encode("utf-8"))


def _embed_bits(pixels: list, binary: str) -> list:
    """Embed binary string into LSB of RGB pixels."""
    index = 0
    for i, pixel in enumerate(pixels):
        if index >= len(binary):
            break
        r, g, b = pixel
        rb = format(r, "08b")
        gb = format(g, "08b")
        bb = format(b, "08b")

        rb = rb[:-1] + (binary[index] if index < len(binary) else "0")
        index += 1
        gb = gb[:-1] + (binary[index] if index < len(binary) else "0")
        index += 1
        bb = bb[:-1] + (binary[index] if index < len(binary) else "0")
        index += 1

        pixels[i] = (int(rb, 2), int(gb, 2), int(bb, 2))
    return pixels


def encode_image(image_path: str, secret_message: str, password: str,
                 output_path):
    """
    Full encode pipeline:
      1. Compute original image hash for integrity.
      2. Derive Fernet key from password + random salt.
      3. Encrypt secret_message.
      4. Build payload: SALT_HEX|HASH|ENCRYPTED_MSG
      5. Embed payload bits into LSBs of image pixels.
      6. Save encoded image.

    Returns output_path.
    """
    

    # 2. Key derivation
    key, salt = derive_key_from_password(password)
    salt_hex = salt.hex()  # 32 chars

    # 3. Encrypt
    fernet = Fernet(key)
    encrypted = fernet.encrypt(secret_message.encode("utf-8")).decode("utf-8")

    # 4. Build payload string: salt_hex|sha256hash|encrypted_data\n
    payload = f"{salt_hex}|{encrypted}\n"

    # 5. Open image
    image = Image.open(image_path).convert("RGB")
    pixels = list(image.getdata())
    width, height = image.size

    # Check capacity
    max_bits = (width * height) * 3
    payload_bits = _text_to_bits(payload)

    # Pad to multiple of 3
    remainder = len(payload_bits) % 3
    if remainder != 0:
        payload_bits += "0" * (3 - remainder)

    if len(payload_bits) > max_bits:
        raise ValueError(
            f"Message too long! Image can hold ~{max_bits // 8 - 100} chars."
        )

    # 6. Embed
    pixels = _embed_bits(pixels, payload_bits)

    encoded_image = Image.new("RGB", (width, height))
    encoded_image.putdata(pixels)
    encoded_image.save(output_path)

    # 🔐 Compute hash of encoded image
    encoded_hash = compute_image_hash(output_path)

    # Save hash to a file (same name + .hash)
    hash_file = output_path + ".hash"
    with open(hash_file, "w") as f:
        f.write(encoded_hash)

    return output_path

   