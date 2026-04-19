# Image Steganography Tool

A desktop application to hide encrypted text inside images and decode it later using a password.

This project uses:
- CustomTkinter for the GUI
- Pillow for image processing
- Cryptography (Fernet + PBKDF2) for message encryption
- PyInstaller for Windows executable packaging

## Key Features

- Password-based encryption before embedding
- LSB steganography (Least Significant Bit) for hiding data in image pixels
- Payload capacity indicator before encoding
- Optional image integrity verification using SHA-256 hash files
- Optional email sending of encoded image
- One-click build script for standalone Windows exe

## Project Structure

- main.py: GUI app entry point and user interaction flow
- encoder.py: encryption + payload creation + embedding into image
- decoder.py: extraction + parsing + decryption
- capacity.py: capacity and usage calculations for selected image
- integrity.py: SHA-256 hash computation and verification
- emailer.py: SMTP email sending with .env credentials
- build_exe.bat: automated PyInstaller build script
- project_info.html: info page opened from the app
- assets/: static resources
- dist/: final packaged executable output
- isolation/: local virtual environment used for builds

## Architecture

The app follows a modular pipeline architecture with UI orchestration:

1. Presentation Layer
- main.py builds the GUI and handles user actions.
- It does not implement crypto/embedding logic directly.
- It calls focused service modules for encode/decode/email/hash operations.

2. Core Processing Layer
- encoder.py handles:
  - Deriving key from password (PBKDF2)
  - Encrypting message (Fernet)
  - Building payload: SALT_HEX|ENCRYPTED_MESSAGE\n
  - Embedding payload bits into RGB LSB channels
- decoder.py handles:
  - Reading LSB bits from encoded image
  - Reconstructing payload text
  - Parsing salt and encrypted token
  - Re-deriving key and decrypting

3. Utility and Security Layer
- capacity.py estimates maximum characters and current usage percent.
- integrity.py computes and verifies SHA-256 of image pixel bytes.
- emailer.py loads SMTP credentials from .env and sends the encoded image.

4. Packaging Layer
- build_exe.bat runs dependency install and PyInstaller build.
- PyInstaller bundles Python runtime and dependencies into dist/ImgStego.exe.

## Encode Flow (High Level)

1. User selects cover image and enters message/password.
2. main.py calls encoder.encode_image(...).
3. encoder.py derives a key from password and random salt.
4. Message is encrypted with Fernet.
5. Payload is converted to bits and embedded in image LSBs.
6. Encoded image is saved.
7. Hash file is generated for optional future integrity check.
8. Optional: emailer.py sends encoded image as attachment.

## Decode Flow (High Level)

1. User selects encoded image and enters password.
2. main.py calls decoder.decode_image(...).
3. decoder.py extracts LSB bits and rebuilds payload text.
4. Salt and encrypted data are parsed.
5. Password-derived key is recreated and used to decrypt.
6. Decoded plaintext is shown in UI.
7. Optional integrity check compares supplied hash with computed hash.

## Run From Source

Use PowerShell from project folder:

```powershell
# Create environment (if needed)
python -m venv isolation

# Activate environment
.\isolation\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run app
python main.py
```

## Build Standalone EXE

Use the build script:

```powershell
.\build_exe.bat
```

Output:
- dist/ImgStego.exe

The generated exe is standalone for target Windows systems (Python installation not required on receiver machine).

## Distribute To Others

Share:
- dist/ImgStego.exe

If receiver needs email feature, place a .env file next to the exe:

```env
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

Without .env, the app still runs; only email sending will fail.

## Development Notes

- You should keep isolation/ for development and rebuilding.
- If you modify code, rebuild exe to include your changes:

```powershell
.\build_exe.bat
```

- The exe is a snapshot of code at build time.

## Security Notes

- Password is not stored by the app.
- Use strong passwords for encryption.
- Share password through a separate communication channel.
- Do not hardcode SMTP credentials in source code.

## Troubleshooting

1. EXE opens slowly first time
- One-file PyInstaller apps unpack at startup. This is expected.

2. Email sending fails
- Verify .env location and values.
- For Gmail, use an App Password (not account password).

3. Build fails
- Activate correct environment.
- Reinstall dependencies with requirements.txt.
- Delete build/ and dist/ and run build_exe.bat again.

## Future Improvements

- Add automated tests for encode/decode round trip
- Add drag-and-drop image support
- Add logging to a file for better diagnostics
- Add digital signature to executable for smoother distribution trust
