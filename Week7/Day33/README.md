
# Week 7 — Day 4: Calendar, Email, CRM & Appointment Workflows

## Overview

Day 4 focused on turning the real estate voice agent from a conversational system into an agent that can perform real-world business actions.

The agent can now:

* Create, update, and delete Google Calendar appointments
* Send appointment notification emails
* Store customer information in a CRM
* Log conversation transcripts
* Book property-viewing appointments end to end
* Reschedule existing appointments
* Cancel existing appointments
* Keep Calendar, Email, and CRM operations connected through a single appointment workflow
* Handle external-service failures without crashing the voice pipeline

The implementation is designed around reusable, independent services with a single integration layer:

```text
                    Voice Agent
                        │
                        ▼
             Appointment Manager
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Calendar        Email          CRM
      Service         Service       Service
          │             │             │
          ▼             ▼             ▼
     Google Calendar   SMTP        SQLite CRM
```

---

# Day 4 Tasks

## Task 1 — Google Calendar Integration

Implemented Google Calendar functionality for appointment management.

### Supported operations

* Create appointment
* Update/reschedule appointment
* Delete/cancel appointment

The Calendar service is implemented independently in:

```text
app/calendar/google_calendar.py
```

The service is reusable and does not contain CRM or email logic.

### Validation

The standalone Calendar test successfully verifies the Google Calendar integration.

A real Calendar event is created during testing and subsequently removed by the test cleanup process.

---

# Task 2 — Email Notifications

Implemented SMTP-based email notifications for appointment workflows.

Location:

```text
app/email/email_service.py
```

Supported notifications:

* New appointment
* Rescheduled appointment
* Cancelled appointment

SMTP configuration is loaded from `.env` through:

```text
app/config.py
```

### Testing

The standalone email test:

```text
test_email.py
```

successfully sent the three notification types.

The test sends real emails to the recipient supplied to the script.

> Production note: employee email addresses in the property database should be verified before enabling real employee notifications.

---

# Task 3 — CRM Integration

Implemented a lightweight SQLite-backed CRM.

Location:

```text
app/crm/crm_service.py
```

The CRM uses the project's existing SQLite database:

```text
database/property_data.db
```

No separate database system was introduced.

The CRM automatically creates the following tables:

```text
crm_clients
crm_transcripts
crm_appointments
```

## CRM capabilities

### Client management

* Create new clients
* Update existing clients
* Deduplicate clients using phone number

### Conversation logging

* Store conversation transcripts
* Retrieve transcript history

### Appointment management

* Create appointments
* Track appointment status
* Reschedule appointments
* Cancel appointments
* Retrieve active appointments
* Retrieve appointment history

### Follow-up support

The CRM also provides:

* Follow-up reminder storage
* Due follow-up lookup

A scheduler is intentionally outside the scope of Day 4.

---

# Task 4 — Appointment Workflow

The three services are integrated through:

```text
app/workflows/appointment_manager.py
```

This module is the central integration point for:

```text
Calendar + Email + CRM
```

The individual services remain independent and reusable.

## Booking workflow

```text
Book Appointment
       │
       ▼
Create / Update CRM Client
       │
       ▼
Log Transcript
       │
       ▼
Find Assigned Property Agent
       │
       ▼
Create Google Calendar Event
       │
       ▼
Send Employee Notification
       │
       ▼
Create CRM Appointment
```

## Rescheduling workflow

```text
Reschedule Request
       │
       ▼
Find Client
       │
       ▼
Find Active Appointment
       │
       ▼
Update Google Calendar Event
       │
       ▼
Send Reschedule Email
       │
       ▼
Update CRM Appointment
```

## Cancellation workflow

```text
Cancellation Request
       │
       ▼
Find Client
       │
       ▼
Find Active Appointment
       │
       ▼
Delete Google Calendar Event
       │
       ▼
Send Cancellation Email
       │
       ▼
Mark CRM Appointment as Cancelled
```

---

# Task 5 — Testing

Day 4 includes separate tests for each service as well as a complete appointment workflow test.

## CRM Test

Run:

```bash
python test_crm.py
```

The test validates:

1. Client insertion
2. Client update/upsert behavior
3. Transcript logging
4. Appointment creation
5. Active appointment lookup
6. Appointment rescheduling
7. Follow-up reminder lookup
8. Appointment cancellation
9. Appointment history

The test also removes its temporary CRM records afterward.

### Result

```text
All CRM tests passed.
OK — test rows removed
```

---

## Email Test

Run:

```bash
python test_email.py <your_test_email>
```

The test validates:

1. Appointment notification
2. Reschedule notification
3. Cancellation notification

These are real SMTP emails.

> Use a test address you can safely check.

---

## Appointment Workflow Test

Run:

```bash
python test_appointments.py
```

This performs the complete integration flow:

```text
Book
 ↓
Reschedule
 ↓
Cancel
 ↓
Cleanup
```

The test uses a clearly marked test client and phone number.

It creates a real Google Calendar event, exercises the email notification path, writes CRM records, and then cleans up the test CRM data.

### Successful test result

```text
=== 1. book_appointment() ===
OK — booked appointment
    assigned_employee=Hassan Raza

=== 2. reschedule_appointment() ===
OK — rescheduled

=== 3. cancel_appointment() ===
OK — cancelled

All appointment workflow tests completed.

=== Cleanup ===
OK — removed test CRM rows
```

---

# Email Delivery Testing Note

During integration testing, the property database contained an assigned employee email address for the test property.

The workflow therefore attempted to send notifications to that address.

The SMTP provider accepted the outgoing message, but delivery failed because the configured employee domain did not exist.

This confirmed an important behavior of the workflow:

> Email delivery failure does not roll back an otherwise successful Calendar/CRM operation.

The system logs the email failure as a warning and continues the workflow.

Before production use, employee email addresses must be replaced with verified, deliverable addresses.

---

# Test Data Cleanup

The integration tests use clearly identifiable test data.

Examples:

```text
TEST — CRM Script
TEST — Appointment Workflow Script
+92-300-TEST-CRM
+92-300-TEST-APPT
```

The CRM tests remove their temporary rows after execution.

The appointment workflow test also removes its CRM records and deletes the Calendar event when necessary.

This prevents test data from permanently polluting the production-style database.

---

# Architecture

Day 4 follows a separation-of-concerns approach:

```text
app/
│
├── calendar/
│   └── google_calendar.py
│
├── email/
│   └── email_service.py
│
├── crm/
│   └── crm_service.py
│
└── workflows/
    └── appointment_manager.py
```

### Responsibilities

| Module                   | Responsibility                       |
| ------------------------ | ------------------------------------ |
| `google_calendar.py`     | Google Calendar operations           |
| `email_service.py`       | SMTP email notifications             |
| `crm_service.py`         | SQLite CRM operations                |
| `appointment_manager.py` | Calendar + Email + CRM orchestration |

This keeps external integrations reusable and prevents duplicated business logic.

---

# Configuration

External services are configured through `.env`.

Typical configuration includes:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=true
```

Google Calendar configuration is also loaded through the project's existing configuration system.

Secrets must **not** be committed to GitHub.

The `.env` file should remain ignored by Git.

---

# Day 4 Deliverables

```text
app/
├── calendar/
│   └── google_calendar.py
├── email/
│   └── email_service.py
├── crm/
│   └── crm_service.py
└── workflows/
    └── appointment_manager.py

tools/
└── appointment_intent.py

tests / test scripts
├── test_calendar.py
├── test_email.py
├── test_crm.py
└── test_appointments.py
```

Additionally, appointment-intent detection was implemented for identifying:

```text
book
reschedule
cancel
```

and extracting appointment-specific details such as:

```text
client name
phone
date
time
property
notes
```

---

# Deferred: n8n Workflow

An n8n workflow has been prepared for external workflow automation:

```text
real_estate_workflow.json
```

The workflow is intended to connect the voice-agent API with the appointment workflow and provide an automation layer around the existing FastAPI endpoints.

However, the n8n workflow is **not considered part of the completed Day 4 validation yet**.

It will be tested separately after the LangGraph orchestration work is completed.

The planned architecture is:

```text
Voice / External Trigger
          │
          ▼
         n8n
          │
          ▼
       FastAPI
          │
          ▼
      LangGraph
          │
          ▼
   Appointment Tools
     ┌────┼────┐
     ▼    ▼    ▼
 Calendar Email CRM
```

n8n therefore complements the agent orchestration rather than replacing LangGraph.

---

# ✅ Day 4 Completion Status

| Component                    | Status        |
| ---------------------------- | ------------- |
| Google Calendar              | ✅ Complete    |
| Email Service                | ✅ Complete    |
| CRM Service                  | ✅ Complete    |
| Appointment Manager          | ✅ Complete    |
| Booking Workflow             | ✅ Tested      |
| Rescheduling Workflow        | ✅ Tested      |
| Cancellation Workflow        | ✅ Tested      |
| CRM Integration Test         | ✅ Passed      |
| Email Integration Test       | ✅ Passed      |
| End-to-End Appointment Test  | ✅ Passed      |
| Appointment Intent Detection | ✅ Implemented |
| n8n Workflow                 | ⏸️ Deferred   |

---

# Outcome

By the end of Day 4, the voice agent is no longer limited to answering questions.

It can now perform real business operations:

```text
Customer
   │
   ▼
Voice Agent
   │
   ├── Understand appointment request
   │
   ├── Create Calendar booking
   │
   ├── Notify assigned employee
   │
   └── Store customer + appointment in CRM
```
