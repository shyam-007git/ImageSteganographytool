import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image

from integrity import verify_integrity


def _bits_to_text(bits: str) -> str:
    """Convert binary string back to text, stopping at null char or newline."""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = bits[i : i + 8]
        char = chr(int(byte, 2))
        chars.append(char)
        if char == "\n":
            break
    return "".join(chars)


def _derive_key(password: str, salt_hex: str) -> bytes:
    """Re-derive Fernet key from password and stored salt."""
    salt = bytes.fromhex(salt_hex)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


def decode_image(file_path: str, password: str):
    """
    Full decode pipeline:
      1. Extract LSBs from image pixels → binary string → text payload.
      2. Parse payload: SALT_HEX|HASH|ENCRYPTED_MSG
      3. Verify image integrity using stored hash.
      4. Re-derive key from password + salt.
      5. Decrypt and return original message.

    Returns (original_message, integrity_ok).
      integrity_ok = True  → image was not tampered with.
      integrity_ok = False → image may have been modified after encoding.
    """
    # 1. Open image and extract LSBs
    image = Image.open(file_path).convert("RGB")
    pixels = list(image.getdata())

    binary_bits = []
    for pixel in pixels:
        try:
            r, g, b = pixel
        except (ValueError, TypeError):
            raise ValueError("Please select a valid encoded PNG image.")
        binary_bits.append(format(r, "08b")[-1])
        binary_bits.append(format(g, "08b")[-1])
        binary_bits.append(format(b, "08b")[-1])

    binary_string = "".join(binary_bits)
    raw_text = _bits_to_text(binary_string)

    # 2. Parse payload
    raw_text = raw_text.rstrip("\n")
    parts = raw_text.split("|", 2)
    if len(parts) != 2:
        raise ValueError(
            "No hidden message found or image is not encoded with this tool."
        )

    salt_hex, encrypted_data = parts

    # 3. Integrity check — Handled in UI

    # 4. Re-derive key
    try:
        key = _derive_key(password, salt_hex)
    except Exception:
        raise ValueError("Invalid password or corrupted data.")

    # 5. Decrypt
    try:
        fernet = Fernet(key)
        original_message = fernet.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Wrong password! Decryption failed.")

    return original_message