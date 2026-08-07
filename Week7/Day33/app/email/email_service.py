"""
app/email/email_service.py
----------------------------

SMTP-based email notifications for appointment booking, rescheduling, and
cancellation, sent to the assigned employee.

Uses Python's stdlib smtplib/email modules rather than the `resend` package
already in requirements.txt — the Day 4 spec explicitly requires SMTP
configuration sourced from .env, a different delivery mechanism than
Resend's API. requirements.txt is left unchanged; smtplib needs no new
dependency.
"""

from __future__ import annotations

import logging
import smtplib
import time
from email.message import EmailMessage

from app import config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 2.0


class EmailServiceError(Exception):
    """Raised when sending an email fails after retries are exhausted."""


def _send(msg: EmailMessage) -> None:
    if not config.SMTP_HOST or not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
        raise EmailServiceError(
            "SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, and "
            "SMTP_PASSWORD in .env."
        )

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
                if config.SMTP_USE_TLS:
                    server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent: %s", msg["Subject"])
            return
        except (smtplib.SMTPException, OSError) as exc:
            last_exc = exc
            if attempt == _MAX_RETRIES:
                break
            wait = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Email send failed (attempt %d/%d), retrying in %.1fs: %s",
                attempt, _MAX_RETRIES, wait, exc,
            )
            time.sleep(wait)

    logger.error("Email send failed after %d attempts: %s", _MAX_RETRIES, last_exc)
    raise EmailServiceError(f"Failed to send email: {last_exc}") from last_exc


def _build_message(to_email: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def send_appointment_notification(
    employee_email: str,
    employee_name: str,
    client_name: str,
    client_phone: str,
    property_name: str,
    meeting_time: str,
    requirements: str = "",
    notes: str = "",
) -> None:
    """Sent when a new appointment is booked."""

    subject = f"New Appointment: {client_name} — {property_name}"
    body = (
        f"Hi {employee_name},\n\n"
        f"A new property viewing has been booked for you.\n\n"
        f"Meeting Time: {meeting_time}\n"
        f"Property: {property_name}\n"
        f"Client: {client_name}\n"
        f"Phone: {client_phone}\n"
        f"Requirements: {requirements or 'N/A'}\n"
        f"Notes: {notes or 'N/A'}\n\n"
        f"— Meridian Homes Pakistan Voice Agent"
    )
    _send(_build_message(employee_email, subject, body))


def send_reschedule_notification(
    employee_email: str,
    employee_name: str,
    client_name: str,
    client_phone: str,
    property_name: str,
    new_meeting_time: str,
    notes: str = "",
) -> None:
    """Sent when an existing appointment is rescheduled."""

    subject = f"Appointment Rescheduled: {client_name} — {property_name}"
    body = (
        f"Hi {employee_name},\n\n"
        f"The appointment below has been rescheduled.\n\n"
        f"New Meeting Time: {new_meeting_time}\n"
        f"Property: {property_name}\n"
        f"Client: {client_name}\n"
        f"Phone: {client_phone}\n"
        f"Notes: {notes or 'N/A'}\n\n"
        f"— Meridian Homes Pakistan Voice Agent"
    )
    _send(_build_message(employee_email, subject, body))


def send_cancellation_notification(
    employee_email: str,
    employee_name: str,
    client_name: str,
    client_phone: str,
    property_name: str,
    original_meeting_time: str,
    notes: str = "",
) -> None:
    """Sent when an appointment is cancelled."""

    subject = f"Appointment Cancelled: {client_name} — {property_name}"
    body = (
        f"Hi {employee_name},\n\n"
        f"The appointment below has been cancelled.\n\n"
        f"Originally Scheduled: {original_meeting_time}\n"
        f"Property: {property_name}\n"
        f"Client: {client_name}\n"
        f"Phone: {client_phone}\n"
        f"Notes: {notes or 'N/A'}\n\n"
        f"— Meridian Homes Pakistan Voice Agent"
    )
    _send(_build_message(employee_email, subject, body))