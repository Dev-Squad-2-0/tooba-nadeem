"""
test_email.py
---------------

Standalone test script for app/email/email_service.py, using SMTP
settings from app/config.py (sourced from .env) UNCHANGED.

Sends REAL emails to the recipient you provide — use an address you can
actually check. If SMTP isn't configured yet, this prints clear setup
instructions instead of a raw traceback.

Usage:
    python test_email.py your_test_email@example.com
"""

import sys

from app.email.email_service import (
    EmailServiceError,
    send_appointment_notification,
    send_cancellation_notification,
    send_reschedule_notification,
)
from app import config


def check_config() -> bool:
    missing = [
        name for name, value in [
            ("SMTP_HOST", config.SMTP_HOST),
            ("SMTP_USERNAME", config.SMTP_USERNAME),
            ("SMTP_PASSWORD", config.SMTP_PASSWORD),
        ]
        if not value
    ]
    if missing:
        print(
            "SMTP is not fully configured. Missing in .env: "
            f"{', '.join(missing)}\n\n"
            "Add to .env:\n"
            "  SMTP_HOST=smtp.gmail.com\n"
            "  SMTP_PORT=587\n"
            "  SMTP_USERNAME=your_email@gmail.com\n"
            "  SMTP_PASSWORD=your_app_password\n"
            "  SMTP_FROM_EMAIL=your_email@gmail.com\n"
            "  SMTP_USE_TLS=true\n\n"
            "For Gmail, SMTP_PASSWORD must be an App Password "
            "(Google Account -> Security -> App Passwords), not your "
            "regular account password."
        )
        return False
    return True


def run(recipient: str):
    if not check_config():
        sys.exit(1)

    print(f"Sending test emails to: {recipient}\n")

    print("=== 1. send_appointment_notification() ===")
    try:
        send_appointment_notification(
            employee_email=recipient,
            employee_name="Test Agent",
            client_name="TEST — Email Script",
            client_phone="+92-300-0000000",
            property_name="Skyline Residency",
            meeting_time="Saturday, 09 August 2026 at 03:00 PM",
            requirements="3 bedroom apartment, DHA Lahore",
            notes="Automated test — safe to ignore.",
        )
        print("OK — sent")
    except EmailServiceError as exc:
        print(f"FAIL — {exc}")
        sys.exit(1)

    print("\n=== 2. send_reschedule_notification() ===")
    try:
        send_reschedule_notification(
            employee_email=recipient,
            employee_name="Test Agent",
            client_name="TEST — Email Script",
            client_phone="+92-300-0000000",
            property_name="Skyline Residency",
            new_meeting_time="Sunday, 10 August 2026 at 04:30 PM",
            notes="Automated test — safe to ignore.",
        )
        print("OK — sent")
    except EmailServiceError as exc:
        print(f"FAIL — {exc}")

    print("\n=== 3. send_cancellation_notification() ===")
    try:
        send_cancellation_notification(
            employee_email=recipient,
            employee_name="Test Agent",
            client_name="TEST — Email Script",
            client_phone="+92-300-0000000",
            property_name="Skyline Residency",
            original_meeting_time="Saturday, 09 August 2026 at 03:00 PM",
            notes="Automated test — safe to ignore.",
        )
        print("OK — sent")
    except EmailServiceError as exc:
        print(f"FAIL — {exc}")

    print(f"\nDone. Check {recipient} for 3 test emails.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_email.py <recipient_email>")
        sys.exit(1)
    run(sys.argv[1])