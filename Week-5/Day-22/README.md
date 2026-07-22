# LangGraph — Stateful, Multi-Step & Cyclical Agent Workflows
**Week 5 • Day 3**

## Overview
This project introduces **LangGraph** by building a stateful workflow for a budget recommendation assistant. Unlike a traditional agent loop, the workflow is represented as a graph of nodes and edges, making branching, looping, persistence, and human approval straightforward to implement.

## Features
- Designed a shared workflow state using `TypedDict`
- Built a linear graph (`plan → retrieve → generate → format`)
- Added conditional routing with a self-correction loop
- Prevented infinite loops using a retry counter
- Implemented Human-in-the-Loop using `interrupt_before`
- Added persistence with `MemorySaver`
- Demonstrated checkpoint recovery and state history debugging
- Generated a Mermaid workflow diagram from the compiled graph

## Workflow

```text
START
  │
  ▼
plan
  │
  ▼
retrieve
  │
  ▼
generate
  │
  ▼
critique
  ├───────────────► generate (if quality is low)
  │
  ▼
send_email (Human Approval)
  │
  ▼
format
  │
  ▼
END
```

## Technologies Used
- Python
- LangGraph
- LangChain Core
- MemorySaver Checkpointer
- Jupyter Notebook

## Learning Outcomes
- Understood LangGraph's core concepts (`StateGraph`, nodes, edges, shared state)
- Built graph-based agent workflows
- Implemented conditional edges and cyclic execution
- Added human approval before a risky action
- Used checkpointing to pause and resume execution
- Explored state history for debugging and replay

## Repository Structure

```
Day-22/
├── LangGraph.ipynb
├── products.json
├── requirements.txt
├── final_workflow.png
└── README.md
```
