# Week 7 — Day 5: LangGraph Orchestration & Tool Calling

## Overview

Day 5 transformed the real estate voice agent from a collection of independent components into a coordinated **LangGraph-based AI agent**.

The graph now manages conversation state, detects user intent, routes requests to the appropriate tools and workflows, validates critical actions, and generates responses based on the actual outcome of those actions.

The system supports real estate conversations involving:

* Property search and recommendations
* Retrieval-Augmented Generation (RAG)
* Appointment booking
* Appointment rescheduling
* Appointment cancellation
* Calendar availability checking
* Google Calendar operations
* CRM operations
* Email notifications
* Conversation/session state
* Missing-information clarification
* Deterministic handling of critical appointment failures
* Annotated graph and tool execution logging

---

# 1. Objectives

The main objectives for Day 5 were:

1. Design a structured LangGraph state.
2. Route conversations through appropriate graph nodes.
3. Integrate business tools into the graph.
4. Prevent the agent from performing invalid actions.
5. Ask for clarification when required information is missing.
6. Log graph transitions and tool execution.
7. Ensure the LLM cannot falsely claim that a failed business action succeeded.

---

# 2. LangGraph State Design

The graph maintains structured state throughout a conversation.

The state includes information such as:

* Conversation/session information
* User profile
* Property preferences
* Budget
* Current property
* Requested appointment date
* Requested appointment time
* Detected intent
* Appointment details
* Tool outputs
* Appointment status
* Missing fields
* Deterministic response overrides

The state allows information collected in one turn to be reused in later turns.

For example:

```text
User:
"My budget is 3 crore."

Later:

"DHA mein kya options hain?"
```

The system can retain the previously extracted budget instead of treating the second message as an entirely new conversation.

---

# 3. Graph Architecture

The agent uses LangGraph to orchestrate the conversation.

A simplified execution flow is:

```text
                    ┌─────────────────┐
                    │   Load State    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Slot Extraction │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Intent Detection│
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   Property Search        Booking          Reschedule
          │                  │                  │
          ▼                  ▼                  ▼
        RAG             Availability       Availability
          │                  │                  │
          ▼                  ▼                  ▼
 Recommendation          Calendar            Calendar
                             │                  │
                             ▼                  ▼
                           CRM                CRM
                             │                  │
                             └────────┬─────────┘
                                      │
                                      ▼
                              Email Notification
                                      │
                                      ▼
                             Response Generation
                                      │
                                      ▼
                                     END
```

The actual route depends on the detected user intent.

---

# 4. Supported Graph Intents

The graph currently handles multiple business intents.

### Property Search

```text
intent_detection
      ↓
recommendation
      ↓
search_property
      ↓
rag_search
      ↓
response_generation
```

### Appointment Booking

```text
intent_detection
      ↓
extract_appointment_details
      ↓
check_missing_fields
      ↓
availability_check
      ↓
booking
      ↓
calendar + CRM + email
      ↓
response_generation
```

### Appointment Rescheduling

```text
intent_detection
      ↓
extract_appointment_details
      ↓
check_missing_fields
      ↓
availability_check
      ↓
reschedule
      ↓
calendar + CRM + email
      ↓
response_generation
```

### Appointment Cancellation

The graph also contains a cancellation workflow that uses appointment details to identify and update the existing appointment.

---

# 5. Tool Integration

Day 5 integrated the following tools into the LangGraph workflow.

## Search Property

Used to find properties from the available property database.

```text
[TOOL] search_property
```

The tool is used before making property-specific recommendations.

---

## RAG Search

The RAG system retrieves relevant company and property knowledge from the knowledge base.

Example log:

```text
INFO:app.rag.retriever:Searching knowledge base...
INFO:app.rag.retriever:Retrieved 5 documents.
```

Retrieved information can include:

* Company information
* Property brochures
* Developers
* Project information
* Amenities
* Other real estate knowledge

---

## Availability Checker

The availability checker verifies whether a requested appointment time is free before booking or rescheduling.

Example:

```text
[GRAPH] availability_check

Availability check for 2026-08-10 17:00 (60 min): available
```

or:

```text
Availability check for 2026-08-10 17:00 (60 min): unavailable
```

This prevents the agent from blindly creating appointments.

---

## Google Calendar

Google Calendar is used for actual appointment operations.

Supported operations include:

* Availability checking
* Creating events
* Updating events
* Deleting/cancelling events

Example:

```text
Created calendar event f6o861j0p63jahei8iugdj40us for Tooba
```

and:

```text
Updated calendar event f6o861j0p63jahei8iugdj40us
```

---

## CRM

The CRM stores appointment/customer information.

The workflow supports operations such as:

* Adding appointments
* Finding customers by phone
* Updating appointment status
* Associating CRM records with calendar events

Example:

```text
[RESCHEDULE] Existing appointment found:
CRM ID=5fff735e-5dcc-4ce6-b6a5-aca07dbbfbd9
```

---

## Email

The email service sends appointment notifications.

For example:

```text
Email sent: New Appointment: Tooba — Skyline Residency
```

and:

```text
Email sent: Appointment Rescheduled: Tooba — Skyline Residency
```

---

# 6. Appointment Workflow

The appointment workflow was tested end-to-end.

A successful booking follows this sequence:

```text
User request
    ↓
Intent = booking
    ↓
Extract appointment details
    ↓
Check missing fields
    ↓
Check calendar availability
    ↓
Create calendar event
    ↓
Create CRM appointment
    ↓
Send notification email
    ↓
Mark booking complete
    ↓
Generate response
```

Example successful execution:

```text
[GRAPH] intent = booking
[GRAPH] check_missing_fields
[GRAPH] missing_fields = []
[GRAPH] availability_check
[TOOL] availability_check -> available
[GRAPH] booking
Created calendar event ...
Email sent: New Appointment: Tooba — Skyline Residency
Booked appointment ... for Tooba
[TOOL] calendar.create_event + crm.add_appointment + email.send -> success
[GRAPH] booking_complete
```

---

# 7. Appointment Rescheduling

Rescheduling was tested with an existing appointment.

The workflow successfully:

1. Identified the reschedule intent.
2. Extracted the new date/time.
3. Retrieved the customer's appointment using the phone number.
4. Checked the new calendar slot.
5. Updated the Google Calendar event.
6. Sent a rescheduling email.
7. Updated the CRM appointment.
8. Returned a successful response.

Example trace:

```text
[GRAPH] intent = reschedule
[GRAPH] extract_appointment_details
[GRAPH] check_missing_fields
[GRAPH] missing_fields = []
[GRAPH] availability_check
[TOOL] availability_check -> available
[GRAPH] reschedule
```

Then:

```text
[RESCHEDULE] Looking up appointment for phone=03041234567
[RESCHEDULE] Existing appointment found
[RESCHEDULE] Updating Calendar event ...
[RESCHEDULE] Calendar update SUCCESS
[RESCHEDULE] Notification email SUCCESS
[RESCHEDULE] CRM update SUCCESS
[RESCHEDULE] COMPLETE
```

This confirms that the rescheduling workflow performs the actual business operation rather than simply generating a conversational confirmation.

---

# 8. Deterministic Failure Handling

An important reliability improvement was implemented during Day 5 testing.

Previously, a failed appointment operation could be passed to the LLM with an instruction such as:

```text
RESCHEDULE FAILED.
Explain honestly that the operation failed.
```

The model could still incorrectly respond as if the appointment had succeeded.

To prevent this, critical failure responses are now handled deterministically.

The graph state contains:

```text
deterministic_response_override
```

When a critical appointment action fails, this field is populated.

The response-generation node checks it before making an LLM call.

Conceptually:

```text
appointment operation
        ↓
     failure
        ↓
deterministic response override
        ↓
response_generation
        ↓
LLM call skipped
        ↓
truthful response returned
```

This makes a false-success response structurally impossible for these failure paths.

The terminal confirms this behavior:

```text
[GRAPH] response_generation
[GRAPH] response_generation: deterministic override used, LLM call skipped
```

---

# 9. Validation and Safety Checks

Day 5 introduced and verified several important validation rules.

## 9.1 Never Book an Unavailable Slot

A booking request was tested against an unavailable time.

The system detected:

```text
[GRAPH] availability_check
[TOOL] availability_check -> unavailable
```

The graph then routed to:

```text
[GRAPH] slot_unavailable
```

Instead of booking the appointment.

The final response was:

```text
Maazrat, 2026-08-10 ko 17:00 baje ka waqt available nahi hai.
Kya aap koi doosra din ya waqt bata sakte hain?
```

The system also used the deterministic response override:

```text
[GRAPH] response_generation: deterministic override used, LLM call skipped
```

### Result

**PASS**

The agent did not create an appointment for an unavailable slot.

---

# 10. Clarification Instead of Guessing

A booking request without the required customer information was tested.

Request:

```text
Mujhe Skyline Residency ka visit book karna hai.
```

The graph extracted:

```text
property = Skyline Residency
```

Then detected missing information:

```text
[GRAPH] missing_fields =
['client_name', 'phone', 'date', 'time']
```

The graph routed to:

```text
[GRAPH] ask_clarification
```

The agent responded by requesting the missing information rather than inventing it.

### Result

**PASS**

The system does not silently guess critical appointment details.

---

# 11. Unsupported Property / Location Validation

The system was also tested with a property request outside the company's Pakistan-based database.

Request:

```json
{
  "session_id": "test_unavailable_property",
  "message": "Mujhe Dubai mein koi property recommend kar dein."
}
```

The response correctly stated that the company does not have projects in Dubai and redirected the customer toward Pakistan-based projects.

Example response:

```text
Dubai mein humari company ki koi project nahi hai,
lekin hum Pakistan mein kai projects offer karte hain.
Aap ke liye Skyline Residency, Emerald Gardens,
ya phir Horizon Business Bay suitable ho sakti hai.
```

The agent did not invent a Dubai property.

### Result

**PASS**

The agent does not fabricate unsupported foreign properties.

---

# 12. State Persistence

Conversation state is maintained by session ID.

For example:

```text
session_id = test_reschedule
```

The system can retain information between turns.

A previous turn may establish:

```text
client_name = Tooba
phone = 03041234567
property = Skyline Residency
```

A later turn can provide:

```text
requested_date = 2026-08-10
requested_time = 17:00
```

The appointment workflow can then combine the available information.

This enables multi-turn conversations instead of requiring every detail to be repeated in every message.

---

# 13. Session Reset

The session reset endpoint is available through:

```text
POST /chat/reset/{session_id}
```

The reset workflow also clears pending appointment details so stale information from an abandoned appointment workflow does not accidentally carry into a new interaction.

---

# 14. State and Tool Logging

The system provides detailed execution traces.

Each request begins with:

```text
[GRAPH] START
```

and proceeds through nodes such as:

```text
[GRAPH] load_state
[GRAPH] intent_detection
[GRAPH] recommendation
[GRAPH] rag
[GRAPH] response_generation
[GRAPH] END
```

Tool calls are explicitly logged:

```text
[TOOL] search_property
[TOOL] rag_search
[TOOL] availability_check
[TOOL] calendar.create_event
[TOOL] crm.add_appointment
[TOOL] email.send
```

Rescheduling provides additional structured tracing:

```text
[RESCHEDULE] Looking up appointment
[RESCHEDULE] Existing appointment found
[RESCHEDULE] Calendar update SUCCESS
[RESCHEDULE] Notification email SUCCESS
[RESCHEDULE] CRM update SUCCESS
[RESCHEDULE] COMPLETE
```

These traces make it possible to diagnose failures without relying only on the final conversational response.

---

# 15. API Verification

The FastAPI application exposes the following relevant endpoints:

```text
GET  /health
POST /chat
POST /chat/reset/{session_id}
POST /properties/match
POST /appointments/book
```

The health endpoint was verified successfully:

```json
{
  "status": "ok"
}
```

The interactive API documentation is available through the local Swagger interface:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

---

# 16. Day 5 Validation Summary

| Requirement                                    | Result |
| ---------------------------------------------- | ------ |
| LangGraph state design                         | ✅ PASS |
| Conversation/session state                     | ✅ PASS |
| Intent detection and routing                   | ✅ PASS |
| Property search tool                           | ✅ PASS |
| RAG search tool                                | ✅ PASS |
| Calendar integration                           | ✅ PASS |
| CRM integration                                | ✅ PASS |
| Email integration                              | ✅ PASS |
| Availability checking                          | ✅ PASS |
| Booking workflow                               | ✅ PASS |
| Rescheduling workflow                          | ✅ PASS |
| Unavailable slot protection                    | ✅ PASS |
| Clarification for missing information          | ✅ PASS |
| Unsupported property/location handling         | ✅ PASS |
| State/node logging                             | ✅ PASS |
| Deterministic critical-action failure handling | ✅ PASS |


**Week 7 — Day 5: LangGraph Orchestration & Tool Calling — COMPLETE ✅**

