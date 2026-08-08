from app.calendar.google_calendar import create_event

event = create_event(
    client_name="TEST CLIENT",
    phone="03000000000",
    assigned_employee="TEST EMPLOYEE",
    property_name="Skyline Residency - TEST",
    date="2026-08-08",
    time_str="15:00",
    notes="Day 4 Calendar integration evidence test.",
)

print("\n=== EVENT CREATED ===")
print("Event ID:", event.get("id"))
print("Summary:", event.get("summary"))
print("Start:", event.get("start"))
print("Calendar URL:", event.get("htmlLink"))
print("=====================\n")