"""
app/crm/crm_service.py
------------------------

CRM logging for the voice agent, backed by the same SQLite database Day 1/2
already use (database/property_data.db via config.SQL_DATABASE_PATH) —
no new storage system introduced, consistent with the existing
database/database.py + database/sql_retriever.py pattern.

Tables are created on first use if they don't already exist, so this
integrates without needing a separate migration step.
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Any

from app import config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_BASE_SECONDS = 0.5


class CRMServiceError(Exception):
    """Raised when a CRM operation fails after retries are exhausted."""


class CRMService:
    """
    Reusable CRM data-access layer. One instance holds one SQLite
    connection, following the same pattern as
    database/sql_retriever.py:SQLRetriever.
    """

    def __init__(self):
        self.conn = sqlite3.connect(config.SQL_DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # --------------------------------------------------
    # Schema
    # --------------------------------------------------

    def _create_tables(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS crm_clients (
                client_id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                budget INTEGER,
                preferred_location TEXT,
                property_type TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crm_transcripts (
                transcript_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                transcript TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES crm_clients(client_id)
            );

            CREATE TABLE IF NOT EXISTS crm_appointments (
                appointment_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                calendar_event_id TEXT,
                property_name TEXT NOT NULL,
                assigned_employee TEXT,
                meeting_time TEXT NOT NULL,
                status TEXT NOT NULL,
                follow_up_reminder TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES crm_clients(client_id)
            );

            CREATE INDEX IF NOT EXISTS idx_crm_clients_phone
                ON crm_clients(phone);
            CREATE INDEX IF NOT EXISTS idx_crm_appointments_client
                ON crm_appointments(client_id);
            """
        )
        self.conn.commit()

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def _execute_with_retries(self, operation_name: str, sql: str, params: tuple = ()) -> None:
        """
        SQLite can raise 'database is locked' under concurrent writes
        (e.g. a voice turn and a reschedule request landing close
        together). Retrying briefly handles this without surfacing a
        crash mid-call.
        """
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                self.conn.execute(sql, params)
                self.conn.commit()
                return
            except sqlite3.OperationalError as exc:
                last_exc = exc
                if "locked" not in str(exc).lower() or attempt == _MAX_RETRIES:
                    logger.error("%s failed: %s", operation_name, exc)
                    raise CRMServiceError(f"{operation_name} failed: {exc}") from exc
                wait = _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "%s: database locked, retrying in %.2fs (attempt %d/%d)",
                    operation_name, wait, attempt, _MAX_RETRIES,
                )
                time.sleep(wait)
        raise CRMServiceError(f"{operation_name} failed: {last_exc}")

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat()

    # --------------------------------------------------
    # Clients
    # --------------------------------------------------

    def get_client_by_phone(self, phone: str) -> dict | None:
        rows = self._query(
            "SELECT * FROM crm_clients WHERE phone = ? ORDER BY created_at DESC LIMIT 1",
            (phone,),
        )
        return rows[0] if rows else None

    def upsert_client(
        self,
        client_name: str,
        phone: str,
        budget: int | None = None,
        preferred_location: str | None = None,
        property_type: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Creates a new client record, or updates the existing one for this
        phone number if already present — phone is treated as the natural
        dedup key, since buyers may call in more than once.
        """

        existing = self.get_client_by_phone(phone)
        now = self._now()

        if existing:
            client_id = existing["client_id"]
            self._execute_with_retries(
                "upsert_client (update)",
                """
                UPDATE crm_clients
                SET client_name = ?,
                    budget = COALESCE(?, budget),
                    preferred_location = COALESCE(?, preferred_location),
                    property_type = COALESCE(?, property_type),
                    notes = COALESCE(?, notes),
                    updated_at = ?
                WHERE client_id = ?
                """,
                (client_name, budget, preferred_location, property_type, notes, now, client_id),
            )
        else:
            client_id = str(uuid.uuid4())
            self._execute_with_retries(
                "upsert_client (insert)",
                """
                INSERT INTO crm_clients
                    (client_id, client_name, phone, budget, preferred_location,
                     property_type, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (client_id, client_name, phone, budget, preferred_location,
                 property_type, notes, now, now),
            )

        return self._query(
            "SELECT * FROM crm_clients WHERE client_id = ?", (client_id,)
        )[0]

    # --------------------------------------------------
    # Transcripts
    # --------------------------------------------------

    def log_transcript(self, client_id: str, transcript: str) -> None:
        """
        Appends one transcript entry for this client. Kept as append-only
        log entries (not one growing text blob) so conversation history
        stays queryable per-call rather than as an unbounded string.
        """
        self._execute_with_retries(
            "log_transcript",
            """
            INSERT INTO crm_transcripts (transcript_id, client_id, transcript, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), client_id, transcript, self._now()),
        )

    def get_transcripts(self, client_id: str) -> list[dict]:
        return self._query(
            "SELECT * FROM crm_transcripts WHERE client_id = ? ORDER BY created_at",
            (client_id,),
        )

    # --------------------------------------------------
    # Appointments
    # --------------------------------------------------

    def add_appointment(
        self,
        client_id: str,
        property_name: str,
        meeting_time: str,
        assigned_employee: str | None = None,
        calendar_event_id: str | None = None,
        notes: str | None = None,
        follow_up_reminder: str | None = None,
    ) -> dict:
        appointment_id = str(uuid.uuid4())
        now = self._now()
        self._execute_with_retries(
            "add_appointment",
            """
            INSERT INTO crm_appointments
                (appointment_id, client_id, calendar_event_id, property_name,
                 assigned_employee, meeting_time, status, follow_up_reminder,
                 notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'booked', ?, ?, ?, ?)
            """,
            (appointment_id, client_id, calendar_event_id, property_name,
             assigned_employee, meeting_time, follow_up_reminder, notes, now, now),
        )
        return self._query(
            "SELECT * FROM crm_appointments WHERE appointment_id = ?",
            (appointment_id,),
        )[0]

    def update_appointment_status(
        self,
        appointment_id: str,
        status: str,
        meeting_time: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """status: 'booked' | 'rescheduled' | 'cancelled'."""
        self._execute_with_retries(
            "update_appointment_status",
            """
            UPDATE crm_appointments
            SET status = ?,
                meeting_time = COALESCE(?, meeting_time),
                notes = COALESCE(?, notes),
                updated_at = ?
            WHERE appointment_id = ?
            """,
            (status, meeting_time, notes, self._now(), appointment_id),
        )
        return self._query(
            "SELECT * FROM crm_appointments WHERE appointment_id = ?",
            (appointment_id,),
        )[0]

    def get_active_appointment_for_client(self, client_id: str) -> dict | None:
        """
        Returns the most recent non-cancelled appointment for this client
        — used by appointment_manager.py to find "the" booking to
        reschedule/cancel when the buyer doesn't give an explicit ID.
        """
        rows = self._query(
            """
            SELECT * FROM crm_appointments
            WHERE client_id = ? AND status != 'cancelled'
            ORDER BY created_at DESC LIMIT 1
            """,
            (client_id,),
        )
        return rows[0] if rows else None

    def get_appointment_history(self, client_id: str) -> list[dict]:
        return self._query(
            "SELECT * FROM crm_appointments WHERE client_id = ? ORDER BY created_at DESC",
            (client_id,),
        )

    def set_follow_up_reminder(self, appointment_id: str, reminder_datetime_iso: str) -> None:
        self._execute_with_retries(
            "set_follow_up_reminder",
            "UPDATE crm_appointments SET follow_up_reminder = ?, updated_at = ? WHERE appointment_id = ?",
            (reminder_datetime_iso, self._now(), appointment_id),
        )

    def get_due_follow_ups(self, as_of_iso: str | None = None) -> list[dict]:
        """
        Returns appointments whose follow_up_reminder timestamp has
        passed and are still active — for a future reminder-dispatch job.
        Not wired to a scheduler here (out of scope for Day 4), but
        exposed as a reusable query.
        """
        as_of = as_of_iso or self._now()
        return self._query(
            """
            SELECT * FROM crm_appointments
            WHERE follow_up_reminder IS NOT NULL
              AND follow_up_reminder <= ?
              AND status != 'cancelled'
            ORDER BY follow_up_reminder
            """,
            (as_of,),
        )

    def close(self) -> None:
        self.conn.close()