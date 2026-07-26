# Week 5 Day 4: CrewAI Multi-Agent Collaboration

## Overview

This task explores multi-agent collaboration using **CrewAI**. A three-agent environmental monitoring crew was developed to demonstrate role specialization, tool assignment, task dependencies, sequential execution, and hierarchical delegation.

## Project Workflow

The crew analyzes an environmental monitoring dataset through three specialized roles:

1. **Environmental Data Quality Specialist**
   - Inspects the dataset for missing values, duplicates, and invalid measurements.

2. **Remote Sensing Analyst**
   - Analyzes NDVI, vegetation health, land cover, rainfall, and surface temperature patterns.

3. **Environmental Assessment Report Writer**
   - Converts the analysis into a concise, stakeholder-ready environmental assessment.

## Execution Strategies

Two CrewAI processes were evaluated:

- **Sequential:** Agents execute in a predefined order, with later tasks receiving outputs from earlier tasks.
- **Hierarchical:** A manager agent delegates work to specialist agents and reviews their outputs.

The sequential workflow completed successfully. The hierarchical workflow encountered a manager delegation validation error, which was recorded as part of the reliability comparison.

## Evaluation

The approaches were compared using:

- Output quality
- Token usage
- Latency
- Reliability
- Implementation complexity

The sequential crew produced a **14/15 quality score** while using **21,326 tokens**. The hierarchical attempt used **40,593 tokens** but did not produce a completed final report.

## Files

- `Day-24-CrewAI.ipynb` – Main implementation notebook
- `environmental_monitoring_dataset.csv` – Sample environmental monitoring dataset
- `Day-24_CrewAI_Comparison_Report.md` – Sequential vs. hierarchical vs. single-agent comparison

## Key Takeaway

For this particular environmental monitoring workflow, **sequential multi-agent collaboration was more practical than hierarchical delegation** because the task naturally follows a fixed sequence of data inspection → analysis → reporting.
