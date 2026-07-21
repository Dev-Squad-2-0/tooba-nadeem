# Week 5 - Day 2: Building an Agent with LangChain

## Overview

This project rebuilds the raw Python ReAct agent from Day 1 using LangChain. The implementation demonstrates how LangChain simplifies agent development through built-in abstractions for tool calling, memory, structured outputs, and agent execution while preserving the same Reason → Act → Observe workflow.

---

## Objectives

- Build a LangChain agent using `ChatOpenAI`
- Create reusable tools with the `@tool` decorator
- Implement tool-calling using `AgentExecutor`
- Add conversation memory for multi-turn interactions
- Produce structured outputs using Pydantic models
- Demonstrate graceful error handling for tool failures
- Compare the LangChain implementation with the raw Python agent from Day 1

---

## Tasks Completed

### Task 1 – Basic LangChain Setup

- Configured `ChatOpenAI` with the provided proxy endpoint
- Created a simple prompt using `ChatPromptTemplate`
- Built an LCEL chain using:

```python
prompt | llm | StrOutputParser()
```

---

### Task 2 – Custom Tools

Implemented multiple tools using the `@tool` decorator:

- `calculator`
- `get_weather`
- `get_product_price`

The product price tool retrieves data from a local `products.json` file, simulating a small product database.

---

### Task 3 – Tool Calling Agent

Built an agent using:

- `create_tool_calling_agent`
- `AgentExecutor`

Verified that the agent could:

- Select the appropriate tool
- Execute multiple tool calls
- Use tool outputs to generate a final answer

Example:

> "What is the price of Laptop A and what would a 15% tax add?"

The agent first retrieved the product price, then invoked the calculator tool before generating the final response.

---

### Task 4 – Conversation Memory

Integrated conversation memory using:

```python
RunnableWithMessageHistory
```

Tested a multi-turn conversation:

1. What is the price of Laptop A?
2. Now compare it to Laptop B.
3. Which one should I recommend to a budget-conscious client?

The agent successfully remembered previous responses and answered follow-up questions using the stored conversation history.

---

### Task 5 – Structured Output & Error Handling

Implemented structured outputs using a Pydantic model:

```python
ProductRecommendation
```

The final response is returned as a validated Python object instead of free-form text.

Implemented a stock lookup tool that raises a `ToolException` for invalid products.

Since LangChain **0.3.30** does not support `handle_tool_error` in the `@tool` decorator, graceful recovery was implemented using a `try/except` block around the agent invocation.

---

## Technologies Used

- Python 3.12
- LangChain 0.3.30
- langchain-openai
- Pydantic
- OpenAI-compatible API Proxy

---

## Project Structure

```
Day-21/
│
├── products.json
├── Week5_Day21.ipynb
├── README.md
└── LangChain_vs_RawPython_Writeup.pdf
```

---

## Key Concepts Learned

- LCEL (LangChain Expression Language)
- Runnable pipelines
- Tool creation with `@tool`
- Tool calling agents
- `AgentExecutor`
- Conversation memory
- Structured outputs
- Pydantic validation
- Tool exception handling

---

## Reflection

Compared with the raw Python implementation, LangChain significantly reduced the amount of boilerplate required to build an agent. Tool registration, structured outputs, conversation memory, and agent execution were provided through reusable abstractions instead of manual implementations.

At the same time, some internal behavior became less transparent. The reasoning loop is managed internally by `AgentExecutor`, making debugging more challenging than the explicit implementation from Day 1. Framework-specific conventions, such as using `ToolException` for tool failures, also require an understanding of LangChain's abstractions.

---

## Author

**Tooba Nadeem**

AI & Data Science Intern

NetixSol Pvt Ltd
