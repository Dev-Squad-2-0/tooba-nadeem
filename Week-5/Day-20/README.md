# Week 5 Day 1 — Agent Foundations

## Objective

This notebook demonstrates how an AI agent works without relying on frameworks. A minimal ReAct-style agent was implemented in raw Python using the Anthropic API. The agent performs iterative reasoning, invokes tools through function calling, processes observations, maintains conversation state, and terminates once a final response is produced.

## Tasks Completed

- Explained the differences between agents, chatbots, and workflows.
- Demonstrated the ReAct (Reason → Act → Observe) reasoning loop.
- Implemented JSON tool schemas for multiple tools.
- Built a raw Python agent loop with iterative tool execution.
- Added conversation memory, working state, and execution logging.
- Explored common failure modes and implemented basic guardrails.

## Technologies Used

- Python
- Anthropic Claude API
- JSON Tool Schemas
- Function Calling
- ReAct Reasoning Pattern
