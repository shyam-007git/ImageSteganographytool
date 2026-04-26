import os
import sys
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def _app_base_dir() -> str:
    """Resolve app directory in source mode and frozen executable mode."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))




def send_email(receiver_email: str, image_path: str, sender_email: str, smtp_password: str):
    if not receiver_email:
        raise ValueError("Receiver email is required.")

    if not sender_email or not smtp_password:
        raise ValueError("Missing Gmail credentials from user input.")
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