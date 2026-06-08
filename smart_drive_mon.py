#!/usr/bin/env python3
import subprocess
import re
import sys

EMAIL_SCRIPT = "/path/to/sendmail.py"   # <-- update this
ALERT_RECIPIENT = "you@example.com"     # <-- update this

def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)

def get_sata_drives():
    drives = []
    output = run(["smartctl", "--scan"])
    for line in output.splitlines():
        if "/dev/" in line and "sat" in line:
            dev = line.split()[0]
            drives.append(dev)
    return drives

def get_smart_attribute(output, attr_name):
    pattern = rf"{attr_name}\s+[\d\-]+\s+[\d\-]+\s+[\d\-]+\s+[\w\-]+\s+(\d+)"
    match = re.search(pattern, output)
    return int(match.group(1)) if match else None

def evaluate_drive(dev):
    try:
        output = run(["smartctl", "-A", dev])
    except Exception as e:
        return None, f"Failed to read SMART data for {dev}: {e}"

    hours = get_smart_attribute(output, "Power_On_Hours")
    realloc = get_smart_attribute(output, "Reallocated_Sector_Ct")

    if hours is None or realloc is None:
        return None, f"Missing SMART attributes for {dev}"

    return {
        "device": dev,
        "hours": hours,
        "reallocated": realloc
    }, None

def send_alert(subject, body):
    subprocess.call([
        "python3",
        EMAIL_SCRIPT,
        "--to", ALERT_RECIPIENT,
        "--subject", subject,
        "--body", body
    ])

def main():
    drives = get_sata_drives()
    if not drives:
        send_alert("SMART Check Error", "No SATA drives detected by smartctl.")
        return

    for dev in drives:
        data, error = evaluate_drive(dev)

        if error:
            send_alert(
                "SMART Drive Evaluation Failed",
                f"Drive: {dev}\nError: {error}"
            )
            continue

        if data["reallocated"] > 1:
            body = (
                f"Drive: {data['device']}\n"
                f"Hours in operation: {data['hours']}\n"
                f"Reallocated sectors: {data['reallocated']}\n"
                f"Threshold exceeded."
            )
            send_alert("SMART Warning: Reallocated Sectors", body)

if __name__ == "__main__":
    main()
