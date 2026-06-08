#!/usr/bin/env python3
import subprocess
import requests
import re
import sys
from pathlib import Path

# Path to your email script
EMAIL_SCRIPT = "/path/to/email_sender.py"

# Email recipient for alerts
ALERT_RECIPIENT = "you@example.com"

# Plex version API
PLEX_API_URL = "https://plex.tv/api/downloads/5.json"

def get_installed_version():
    """Get the installed Plex version"""
    try:
        output = subprocess.check_output(
            ["plexmediaserver", "--version"],
            stderr=subprocess.STDOUT,
            text=True
        )
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
        return match.group(1) if match else None
    except Exception:
        return None

def get_latest_version():
    """Fetch the latest Plex version from the API."""
    try:
        data = requests.get(PLEX_API_URL, timeout=5).json()
        return data["computer"]["Linux"]["version"]
    except Exception:
        return None

def is_service_running():
    """Check if PlexMediaServer.service is active."""
    try:
        subprocess.check_call(
            ["systemctl", "is-active", "--quiet", "PlexMediaServer.service"]
        )
        return True
    except subprocess.CalledProcessError:
        return False

def send_alert(subject, body):
    """Send an email alert using the external email script."""
    subprocess.call([
        "python3",
        EMAIL_SCRIPT,
        "--to", ALERT_RECIPIENT,
        "--subject", subject,
        "--body", body
    ])

def main():
    installed = get_installed_version()
    latest = get_latest_version()
    running = is_service_running()

    problems = []

    if installed is None:
        problems.append("Could not detect installed Plex version.")
    elif latest is None:
        problems.append("Could not fetch latest Plex version.")
    elif installed != latest:
        problems.append(f"Plex is outdated: installed {installed}, latest {latest}")

    if not running:
        problems.append("PlexMediaServer.service is NOT running")

    if problems:
        subject = "Plex Server Alert"
        body = "\n".join(problems)
        send_alert(subject, body)
        print("Alert sent.")
    else:
        print("Plex is healthy.")

if __name__ == "__main__":
    main()
