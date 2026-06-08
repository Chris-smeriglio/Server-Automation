#!/usr/bin/env python3
import smtplib
import mimetypes
import argparse
from email.message import EmailMessage
from pathlib import Path

CONFIG_PATH = "./email.conf"   # <-- change if you want

def load_config(path):
    config = {}
    with open(path, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value.strip("\"")

        for key in config:
            print (f"Loaded config: {key} = {config[key]}")
    return config

def send_email(subject, to_addr, body, attachments=None):
    cfg = load_config(CONFIG_PATH)

    gmail_email = cfg.get("email")
    gmail_password = cfg.get("password")

    if not gmail_email or not gmail_password:
        raise ValueError("email.conf missing 'email' or 'password' entries")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_email
    msg["To"] = to_addr
    msg.set_content(body)

    # Attach files
    if attachments:
        for file_path in attachments:
            print(f"Processing attachment: {file_path}")
            path = Path(file_path)
            if not path.exists():
                print(f"Warning: attachment not found: {file_path}")
                continue

            mime_type, _ = mimetypes.guess_type(path)
            mime_type = mime_type or "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)

            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=path.name
                )

    # Connect to Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail_email, gmail_password)
    server.send_message(msg)
    server.quit()


def parse_args():
    parser = argparse.ArgumentParser(description="Send email via Gmail SMTP")

    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--body", required=True, help="Email message body")
    parser.add_argument("--attach", action="append",
                        help="Attachment file path (can be used multiple times)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    send_email(
        subject=args.subject,
        to_addr=args.to,
        body=args.body,
        attachments=args.attach
    )
