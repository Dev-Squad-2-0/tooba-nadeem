# Week 5 Day 1 – Agent Foundations

## Objective

This project demonstrates how an AI agent works without relying on agent frameworks such as LangChain or CrewAI. A minimal ReAct-style agent was implemented in raw Python using NetixSol's OpenAI-compatible LLM endpoint. The agent performs iterative reasoning, invokes tools through function calling, processes observations, maintains conversation state, and continues until it produces a final response.

## Tasks Completed

- Explained the differences between chatbots, workflows, and agents.
- Demonstrated the ReAct (Reason → Act → Observe) reasoning loop.
- Implemented multiple tools using JSON schemas.
- Built a raw Python agent loop with iterative tool execution.
- Added conversation memory, working memory (scratchpad), and execution logging.
- Tested multi-step tool calling with a weather comparison example.
- Explored common failure modes and implemented basic guardrails.

## Project Structure

```
agent_foundations.ipynb   # Complete notebook containing all tasks
writeup.pdf               # One-page project write-up
requirements.txt          # Python dependencies
sample.txt                # Sample file for the file reader tool
.env.example              # Environment variable template
```

## Technologies Used

- Python 3
- OpenAI-Compatible Chat Completions API (NetixSol LLM Endpoint)
- JSON Tool Schemas
- Function Calling
- ReAct Reasoning Pattern

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file using `.env.example` and add your API key.

3. Open `agent_foundations.ipynb` and run the notebook from top to bottom.

## Features

- Raw Python implementation (no agent frameworks)
- Multi-tool support
- JSON schema-based tool definitions
- Conversation memory and working memory
- Iterative reasoning loop
- Logging for reasoning, tool calls, and observations
- Guardrails for common failure scenarios
