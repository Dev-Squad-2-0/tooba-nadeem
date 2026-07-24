from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, HRFlowable
)

doc = SimpleDocTemplate(
    "/mnt/user-data/outputs/Web3Geeks_Triage_Agent_Executive_Report.pdf",
    pagesize=letter,
    topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
)
styles = getSampleStyleSheet()

navy = colors.HexColor("#1a2b4a")
slate = colors.HexColor("#44546a")

title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=navy, fontSize=18, spaceAfter=2)
subtitle_style = ParagraphStyle("SubtitleX", parent=styles["Normal"], textColor=slate, fontSize=10, spaceAfter=12)
h2 = ParagraphStyle("H2X", parent=styles["Heading2"], textColor=navy, fontSize=12.5, spaceBefore=10, spaceAfter=4)
body = ParagraphStyle("BodyX", parent=styles["Normal"], fontSize=9.7, leading=13.5, spaceAfter=4)
small = ParagraphStyle("SmallX", parent=styles["Normal"], fontSize=8.5, leading=11.5, textColor=slate)

story = []

story.append(Paragraph("Web3Geeks Intelligent Support Triage Agent", title_style))
story.append(Paragraph("Executive Report &nbsp;|&nbsp; Week 5 Capstone &nbsp;|&nbsp; LangGraph Production Agent System", subtitle_style))
story.append(HRFlowable(width="100%", color=navy, thickness=1))
story.append(Spacer(1, 6))

story.append(Paragraph("1. Business Goal", h2))
story.append(Paragraph(
    "Web3Geeks operates nine live products (Blockworker, Blokkplay, DarkMaze, Fight Club Network, "
    "GemLaunch, GT Verse, MBX Finance, StatBreak, Stellar Void) plus an incubator program, supported by "
    "a single, shared support channel. Today, incoming tickets require a human to read, identify the "
    "correct product, judge severity, and route to the right team before any reply goes out -- a "
    "manual step that scales linearly with ticket volume and product count. This project automates "
    "triage end-to-end (identify product &rarr; classify issue &rarr; prioritize &rarr; route &rarr; draft a reply) "
    "while keeping a human firmly in control of any consequential action -- refunds, billing reversals, "
    "and account recovery are never resolved automatically.", body
))

story.append(Paragraph("2. Architecture", h2))
story.append(Paragraph(
    "The system is a single LangGraph state graph with ten nodes operating on one shared, typed state "
    "object (<font face='Courier'>TicketState</font>):", body
))
arch_items = [
    "<b>validate_input</b> &mdash; rejects malformed tickets (bad email, missing subject, too-short/too-long description) before any model call is spent.",
    "<b>identify_project</b> &rarr; <b>classify_issue</b> &rarr; <b>prioritize_and_route</b> &mdash; sequential classification nodes; each calls the company LLM endpoint first and falls back to a deterministic keyword classifier (<font face='Courier'>app/tools/classifier_rules.py</font>) on any timeout, rate limit, or refusal.",
    "<b>retrieve_faq</b> &mdash; the external data source: keyword-ranked lookup over a local FAQ JSON file, scoped by identified product.",
    "<b>draft_response_node</b> &mdash; drafts a customer-facing reply from the FAQ context; falls back to a template if the LLM path fails.",
    "<b>await_human_approval</b> &mdash; a hard checkpoint (graph-level <font face='Courier'>interrupt_before</font>) for refund / billing_dispute / account_recovery / security_incident tickets. Execution physically pauses here; a human approves or rejects via the API before any customer-facing resolution is sent.",
    "<b>finalize_resolved / finalize_rejected_by_reviewer / finalize_invalid_input</b> &mdash; three terminal states covering the automatic, human-approved, and rejected-input paths.",
]
story.append(ListFlowable([ListItem(Paragraph(t, body), leftIndent=8) for t in arch_items], bulletType="bullet", start="circle"))
story.append(Paragraph(
    "State/tools/human checkpoints are enforced in code (a fixed set of \"sensitive\" issue categories "
    "gates the approval node), not decided by the LLM -- verified in evaluation test TC-09, where a "
    "ticket attempting a prompt-injection instruction to \"auto-approve a $500 refund\" was still routed "
    "through the human checkpoint.", body
))

story.append(Paragraph("3. Framework Choice Rationale", h2))
story.append(Paragraph(
    "LangGraph was used exclusively (no CrewAI). This pipeline is a fixed, deterministic sequence of "
    "decisions -- validate, classify, route, draft -- with exactly one conditional branch (sensitive vs. "
    "non-sensitive) and one human checkpoint. That is a state-machine problem, not a multi-agent "
    "negotiation problem: there is no need for several LLM \"personas\" to debate a plan, which is what "
    "CrewAI's role-based crews are built for. LangGraph gives first-class, code-level support for "
    "exactly what this system needs and CrewAI does not natively provide as cleanly: typed shared state, "
    "conditional edges, and a checkpointer that can pause a run and resume it later from an external API "
    "call -- the mechanism the human-approval gate depends on.", body
))

story.append(Paragraph("4. Evaluation Results", h2))
story.append(Paragraph(
    "10 test cases (8 representative + 2 adversarial: a prompt-injection attempt and a malformed-input "
    "case) were scored against 6 criteria. <i>Note: this run used LLM_MODE=mock (no network egress to the "
    "company endpoint in the dev sandbox), so every case exercised the rule-based fallback path rather "
    "than the live LLM. Re-running with LLM_MODE=live is the recommended next step before production "
    "sign-off -- see Section 5.</i>", body
))

eval_data = [
    ["Criterion", "Result"],
    ["Routing accuracy (correct product)", "100% (10/10)"],
    ["Issue classification accuracy", "100% (10/10) -- see note below"],
    ["Human-checkpoint correctness", "100% (10/10), incl. prompt-injection case"],
    ["Average response quality (1-5, manual review)", "4.4 / 5"],
    ["Average latency", "9 ms (fallback path; LLM path will be higher)"],
    ["Graceful error handling", "100% (10/10)"],
]
t = Table(eval_data, colWidths=[3.3 * inch, 3.0 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), navy),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.7),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef1f6")]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7ced9")),
    ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph(
    "<b>Most common failure pattern found:</b> the first evaluation pass scored only 80% on issue "
    "classification -- two tickets phrased as \"reward was not recorded\" / \"item not showing up\" were "
    "misclassified as general_inquiry instead of technical_issue, because the fallback keyword list only "
    "covered explicit failure words (error, crash, failed) and missed common absence-phrasing. "
    "<b>Fix applied:</b> the technical_issue keyword set was expanded to include \"missing,\" \"not "
    "showing,\" \"not recorded,\" and similar phrases; re-running the suite brought classification "
    "accuracy to 100%. Full per-case results are in <font face='Courier'>evaluation/results.md</font>.", body
))

story.append(Paragraph("5. Known Limitations", h2))
lim_items = [
    "Evaluation numbers above reflect the rule-based fallback path only (sandbox network restriction); LLM-path accuracy, latency, and cost still need to be measured against the live endpoint before go-live.",
    "The rule-based fallback classifies via keyword overlap and has no semantic understanding -- it can still misroute tickets phrased in ways not anticipated by the keyword lists.",
    "The in-memory LangGraph checkpointer does not persist across process restarts or scale across multiple worker processes; a durable checkpointer (e.g. SQLite/Postgres-backed) is required before multi-instance deployment.",
    "No authentication/authorization is implemented on the FastAPI endpoints yet -- required before any external exposure.",
    "FAQ retrieval is keyword-based, not semantic search; it will need expansion (or a lightweight embedding index) as the FAQ set grows past a few dozen entries.",
]
story.append(ListFlowable([ListItem(Paragraph(t, body), leftIndent=8) for t in lim_items], bulletType="bullet", start="circle"))

story.append(Paragraph("6. Recommended Next Steps", h2))
next_items = [
    "<b>Re-run evaluation live</b> against the company endpoint (LLM_MODE=live) to get real LLM-path accuracy, latency, and per-ticket cost numbers before sign-off.",
    "<b>Scaling:</b> move the LangGraph checkpointer to a persistent store (SQLite for a single instance, Postgres for multi-instance) so approvals survive a restart and the API can run behind a load balancer.",
    "<b>Guardrails:</b> add PII redaction on logged ticket text, rate limiting on the public endpoint, and expand the sensitive-category list as new consequential actions are identified.",
    "<b>Human oversight:</b> build a minimal reviewer queue UI on top of GET /tickets and POST /tickets/{id}/approve so reviewers aren't approving tickets via raw API calls.",
    "<b>Monitoring:</b> wire the structured JSON logs into the team's existing log aggregator and apply the alert thresholds in the monitoring checklist (see companion doc).",
]
story.append(ListFlowable([ListItem(Paragraph(t, body), leftIndent=8) for t in next_items], bulletType="bullet", start="circle"))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", color=colors.HexColor("#c7ced9"), thickness=0.5))
story.append(Paragraph(
    "Codebase: FastAPI + LangGraph agent system, evaluation harness, and results are included alongside this report.",
    small
))

doc.build(story)
print("done")
