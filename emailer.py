import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_email(receiver_email: str, image_path: str):
    """
    Send the encoded image to receiver_email.
    Credentials are read from .env:
      SMTP_EMAIL    - your Gmail address
      SMTP_PASSWORD - your Gmail App Password
    """
    sender_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not smtp_password:
        raise ValueError(
            "Email credentials missing!\n"
            "Add SMTP_EMAIL and SMTP_PASSWORD to your .env file."
        )

    subject = "Encrypted Steganography Image"
    body = (
        "Hello,\n\n"
        "Please find the steganography-encoded image attached.\n\n"
        "To decode it:\n"
        "  1. Open the Steganography Tool.\n"
        "  2. Go to the Decode tab.\n"
        "  3. Load the attached image.\n"
        "  4. Enter the agreed password.\n\n"
        "Note: The password was shared with you separately.\n\n"
        "— Steganography Tool"
    )

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(image_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(image_path))
    part["Content-Disposition"] = (
        f'attachment; filename="{os.path.basename(image_path)}"'
    )
    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, smtp_password)
    try:
        server.send_message(msg)
    except smtplib.SMTPRecipientsRefused:
        raise ValueError(f"Invalid recipient email address: {receiver_email}")
    finally:
        server.quit()