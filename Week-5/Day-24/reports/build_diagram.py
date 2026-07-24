import graphviz

g = graphviz.Digraph("architecture", format="png")
g.attr(rankdir="TB", bgcolor="white", fontname="Helvetica", splines="ortho")
g.attr("node", fontname="Helvetica", fontsize="11", style="filled")

# Graph nodes (LangGraph nodes)
g.node("start", "Support Ticket\n(customer_email, subject, description)", shape="oval",
       fillcolor="#eef1f6", color="#44546a")
g.node("validate", "validate_input\n(reject bad input)", shape="box", fillcolor="#d6e4f0", color="#1a2b4a")
g.node("project", "identify_project\nLLM + rule-based fallback", shape="box", fillcolor="#d6e4f0", color="#1a2b4a")
g.node("issue", "classify_issue\nLLM + rule-based fallback", shape="box", fillcolor="#d6e4f0", color="#1a2b4a")
g.node("route", "prioritize_and_route\nLLM + rule-based fallback", shape="box", fillcolor="#d6e4f0", color="#1a2b4a")
g.node("faq", "retrieve_faq\n(tool: local FAQ JSON)", shape="box", fillcolor="#e2ecd8", color="#3f6b2e")
g.node("draft", "draft_response_node\nLLM + template fallback", shape="box", fillcolor="#d6e4f0", color="#1a2b4a")
g.node("gate", "await_human_approval\n[INTERRUPT — pauses run]", shape="box", fillcolor="#f6dede", color="#8a1f1f")
g.node("resolved", "finalize_resolved", shape="box", fillcolor="#eef1f6", color="#44546a")
g.node("rejected_rev", "finalize_rejected_by_reviewer", shape="box", fillcolor="#eef1f6", color="#44546a")
g.node("rejected_input", "finalize_invalid_input", shape="box", fillcolor="#eef1f6", color="#44546a")

# Tools / data sources (external to the graph)
g.node("projects_db", "projects.json\n(department + escalation map)", shape="cylinder",
       fillcolor="#fbf3d9", color="#8a6d1f")
g.node("faq_db", "faq.json\n(FAQ knowledge base)", shape="cylinder", fillcolor="#fbf3d9", color="#8a6d1f")
g.node("llm", "Company LLM endpoint\n(smart / smart-lite / fast)", shape="component",
       fillcolor="#fbf3d9", color="#8a6d1f")
g.node("api", "FastAPI\nPOST /tickets\nGET /tickets/{id}\nPOST /tickets/{id}/approve", shape="box3d",
       fillcolor="#eef1f6", color="#44546a")
g.node("human", "Human Reviewer\n(support lead)", shape="oval", fillcolor="#f6dede", color="#8a1f1f")

g.edge("start", "api")
g.edge("api", "validate")
g.edge("validate", "rejected_input", label="invalid")
g.edge("validate", "project", label="valid")
g.edge("project", "issue")
g.edge("issue", "route")
g.edge("route", "faq")
g.edge("faq", "draft")
g.edge("draft", "gate", label="sensitive\n(refund/billing/\naccount recovery)")
g.edge("draft", "resolved", label="non-sensitive")
g.edge("gate", "human", style="dashed", label="pauses for")
g.edge("human", "gate", style="dashed", label="approve/reject\n(via API)")
g.edge("gate", "resolved", label="approved")
g.edge("gate", "rejected_rev", label="rejected")

g.edge("project", "projects_db", style="dotted", dir="both")
g.edge("route", "projects_db", style="dotted", dir="both")
g.edge("faq", "faq_db", style="dotted", dir="both")
g.edge("project", "llm", style="dotted", dir="both")
g.edge("issue", "llm", style="dotted", dir="both")
g.edge("route", "llm", style="dotted", dir="both")
g.edge("draft", "llm", style="dotted", dir="both")

g.render("/home/claude/web3geeks-triage/reports/architecture_diagram", cleanup=True)
print("rendered")
