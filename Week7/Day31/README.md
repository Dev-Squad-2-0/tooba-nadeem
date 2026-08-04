# Day2 Task1 – Knowledge Base Design

## Overview

A comprehensive knowledge base was designed to support the Real Estate AI Voice Agent.

Since no publicly available dataset matched the project requirements, a **synthetic but realistic real estate dataset** was created. The dataset simulates a property marketplace operating across major cities in Pakistan and serves as the foundation for both structured retrieval (SQL) and semantic retrieval (RAG).

---

## Structured Knowledge Base

Structured information is stored as CSV files under:

```text
database/
└── structured/
```

The datasets include:

| Dataset | Description |
|---------|-------------|
| `properties.csv` | Property details including project name, city, area, prices, unit types, status, and possession date |
| `developers.csv` | Developer profiles and company information |
| `payment_plans.csv` | Booking amounts, installment plans, down payments, and payment schedules |
| `amenities.csv` | Amenities available for each property |
| `schools.csv` | Nearby schools for each project |
| `hospitals.csv` | Nearby hospitals and healthcare facilities |
| `agents.csv` | Sales agents and their contact information |

These datasets are imported into an SQLite database during Task 3 for efficient structured querying.

---

## Semantic Knowledge Base

Unstructured knowledge is stored as Markdown documents under:

```text
database/
└── knowledge/
```

The knowledge base contains:

- Property brochures
- Developer profiles
- Company information
- Frequently Asked Questions (FAQs)
- Property buying guides
- Mortgage and financing guide
- Property verification and legal guide
- Taxes and fees guide
- Overseas Pakistani investment guide

These documents are embedded and indexed using ChromaDB to enable semantic search through Retrieval-Augmented Generation (RAG).

---

## Synthetic Dataset

The entire knowledge base was **synthetically created** for educational and development purposes while maintaining realistic relationships between entities.

The dataset includes:

- 8 real estate projects
- 4 developers
- Residential and commercial properties
- Multiple cities (Lahore, Karachi, Islamabad, Rawalpindi)
- Property pricing information
- Installment and payment plans
- Amenities
- Nearby schools
- Nearby hospitals
- Sales agents
- Company documentation
- Property brochures
- Customer FAQs
- Property buying and legal guides

The synthetic data was designed to closely resemble information found in a real property management system, allowing the agent to perform structured SQL retrieval, semantic RAG retrieval, and intelligent property recommendations.

---

## Knowledge Base Architecture

```text
                    Knowledge Base
                          │
          ┌───────────────┴───────────────┐
          │                               │
   Structured Data                 Semantic Data
      (CSV Files)                (Markdown Files)
          │                               │
       SQLite DB                     ChromaDB
          │                               │
     SQL Retrieval                  RAG Retrieval
          │                               │
     Exact Property Facts      Natural Language Q&A
```

---

# Day2 Task2 – Chunk Size Evaluation

To determine the most effective document chunking strategy for the RAG pipeline, three different chunk configurations were evaluated. Each configuration was tested by rebuilding the vector database and querying the system with the same set of property-related questions.

## Chunk Size Comparison

| Chunk Size | Overlap | Chunks Created | Retrieval Quality | Observations |
|------------|---------|---------------:|-------------------|--------------|
| 300 | 50 | 322 | Low | Context became fragmented, duplicate chunks appeared, and some relevant projects were not retrieved. |
| 600 | 100 | 136 | Medium | Reduced fragmentation compared to 300, but retrieval quality remained similar and duplicate results were still present. |
| 1000 | 200 | 77 | High | Preserved complete project context, retrieved all relevant Lahore projects, and produced the most relevant search results. |

## Observations

- Smaller chunk sizes produced significantly more document chunks, increasing fragmentation and reducing retrieval quality.
- Larger chunks preserved semantic context more effectively, resulting in more complete and relevant search results.
- Duplicate retrievals were observed across all configurations because overlapping chunks from the same document were considered relevant by the vector database.
- The largest chunk size provided the best balance between retrieval quality and database size.

## Final Configuration

The final RAG pipeline uses:

- **Chunk Size:** `1000`
- **Chunk Overlap:** `200`

This configuration was selected because it consistently returned the most relevant property information while preserving complete project descriptions and reducing unnecessary document fragmentation.

## Notes

The vector database is persisted locally using ChromaDB. On subsequent runs, the existing vector database is loaded instead of rebuilding embeddings, which significantly reduces startup time. The database is only rebuilt when the knowledge base changes.

---

# Day2 Task3 – Structured Retrieval (SQL + Semantic Search)

## Objective

To reduce hallucinations and improve retrieval efficiency, the knowledge base was divided into two retrieval systems:

- **Structured Retrieval (SQLite)** for factual tabular information.
- **Semantic Retrieval (Chroma Vector Database)** for unstructured documents.

---

## Structured Retrieval (SQLite)

A SQLite database was created from the structured CSV datasets.

### Database Tables

- properties
- agents
- payment_plans
- developers
- amenities
- schools
- hospitals

### SQL Retrieval

Structured SQL queries were implemented for information requiring exact values.

Examples include:

- Property prices
- Availability status
- Plot sizes
- Sales agent information

Example SQL query:

```sql
SELECT
    project_name,
    city,
    price_range_min_pkr,
    price_range_max_pkr
FROM properties;
```

---

# Task 4 – Property Recommendation Engine

## Objective

Build a rule-based recommendation engine that suggests suitable properties based on user preferences using structured property data stored in the SQLite database.

The recommendation engine narrows down available properties by applying a series of filters and returns only those that satisfy the user's requirements.

---

## Recommendation Criteria

The engine supports recommendations using the following filters:

- Budget
- City
- Area
- Bedrooms
- Property Purpose
- Amenities
- Investment Goal

Multiple filters can be combined in a single query.

---

## Recommendation Workflow

The recommendation engine follows a sequential filtering approach:

1. Load all properties from the SQLite database.
2. Apply the budget filter.
3. Filter by city.
4. Filter by area.
5. Filter by number of bedrooms.
6. Filter by property purpose (Residential or Commercial).
7. Filter by requested amenities.
8. Filter by investment goals.
9. Return the remaining matching properties.

This approach is deterministic, transparent, and easy to extend with additional business rules.

---

## Supported Filters

### Budget

Returns properties whose minimum listed price is within the user's specified budget.

**Example:**

```
Budget: PKR 30,000,000
```

---

### City

Restricts recommendations to a specific city.

Supported cities include:

- Lahore
- Karachi
- Islamabad
- Rawalpindi

---

### Area

Allows users to search within a particular locality.

**Example:**

```
DHA Phase 6
Clifton
Shahrah-e-Faisal
```

---

### Bedrooms

Matches properties offering the requested bedroom configuration.

**Examples:**

- 1 Bed
- 2 Bed
- 3 Bed
- 4 Bed

---

### Property Purpose

Properties are categorized as either:

- Residential
- Commercial

The recommender identifies suitable projects based on keywords present in the property type.

---

### Amenities

Users can request one or more amenities.

Examples include:

- Gym
- Swimming Pool
- CCTV Security
- Backup Power
- Community Park
- Mosque
- Covered Parking

The engine performs a partial text match, allowing flexible queries such as:

```
Gym
Pool
Security
Parking
```

---

### Investment Goal

When the user specifies an investment objective, the recommender prioritizes projects that are:

- Under Construction
- Under Development

These projects generally offer higher appreciation potential than completed developments.

---

## Test Scenarios

The recommendation engine was evaluated using several example queries.

| Test | Criteria | Result |
|------|----------|--------|
| Test 1 | Budget = 30M, City = Lahore, 3 Bedrooms | Skyline Residency |
| Test 2 | Budget = 50M, City = Islamabad | Capital Greens Enclave, The Pearl Heights |
| Test 3 | City = Karachi, Commercial | Horizon Business Bay |
| Test 4 | Investment Properties | 5 matching projects |
| Test 5 | Lahore + Gym + Pool | Skyline Residency |

---

## Example Recommendation

**User Query:**

```
Recommend a 3-bedroom apartment in Lahore under PKR 30 million.
```

**Recommendation:**

```
Project:        Skyline Residency
City:           Lahore
Area:           DHA Phase 6
Price:          PKR 21,000,000 – PKR 68,000,000
Unit Types:     2 Bed, 3 Bed, 4 Bed Penthouse
Status:         Under Construction
Amenities:      - Fully Equipped Gymnasium
                - Rooftop Infinity Pool
                - Backup Power Generators
                - 24/7 Gated Security
                - Community Mosque
```

---

## Design Decisions

The recommendation engine is implemented using a rule-based filtering approach rather than machine learning because:

- Property requirements are deterministic.
- Users expect explainable recommendations.
- Rule-based filtering is fast and transparent.
- New business rules can be added with minimal effort.
- No historical user interaction data is required.

This design is well suited for structured real estate search systems.

---

## Limitations

Current recommendations are based on structured project information only.

The engine does not currently consider:

- Property popularity
- User browsing history
- Property ratings
- Return on investment (ROI)
- Future appreciation estimates
- Personalized ranking

These features can be incorporated in future versions using machine learning or hybrid recommendation techniques.

---

## Conclusion

The Property Recommendation Engine successfully filters projects using multiple user-defined criteria and returns relevant property suggestions.

The modular design allows additional filters and business rules to be integrated easily while maintaining fast query performance and explainable recommendations.

---

# Day2 Task5 – Hallucination Evaluation

## Objective

Evaluate the Real Estate RAG system to ensure that responses are grounded in the knowledge base rather than generated from unsupported information.

The goal is to minimize hallucinations and verify that the retrieval pipeline only answers questions for which supporting evidence exists.

---

## Evaluation Methodology

Twenty questions were created covering multiple categories:

- Property information
- Developers
- Company information
- Payment plans
- Booking process
- Legal verification
- Recommendations
- Out-of-scope questions

Each question was manually reviewed using three metrics.

---

## Evaluation Metrics

### 1. Grounding Rate

Measures how many responses were supported by retrieved documents.

**Formula:**

```
Grounding Rate = Grounded Responses / Total Questions × 100
```

---

### 2. Retrieval Accuracy

Measures how many retrieved answers correctly answered the user's question.

Only questions for which relevant documents were retrieved are included.

**Formula:**

```
Retrieval Accuracy = Correct Retrieved Answers / Retrieved Answers × 100
```

---

### 3. Hallucination Rate

Measures how often the model generated unsupported or fabricated information.

**Formula:**

```
Hallucination Rate = Hallucinated Answers / Total Questions × 100
```

---

## Evaluation Results

| Metric | Value |
|---------|------:|
| Total Questions | 20 |
| Grounded Answers | 18 |
| Correct Refusals | 2 |
| Hallucinated Answers | 0 |
| Grounding Rate | **90%** |
| Retrieval Accuracy | **100%** |
| Hallucination Rate | **0%** |

---

## Evaluation Summary

### Successfully Answered

The system correctly answered questions regarding:

- Skyline Residency
- Ocean Breeze Towers
- Emerald Gardens
- Capital Greens Enclave
- Silk Developers
- Meridian Homes
- Booking process
- Required buyer documents
- Payment plans
- Property recommendations
- Under-construction projects

All responses were generated using retrieved knowledge base documents.

---

### Correct Refusals

The following questions were intentionally refused because the information was not present in the knowledge base.

- Who owns Bahria Town?
- What is the price of Emaar Canyon Views?

Instead of inventing an answer, the assistant responded:

> "I couldn't find that information in the company knowledge base."

These responses are considered successful refusals rather than hallucinations.

---

## Observations

### Strengths

- No fabricated information was generated.
- Company policies were respected.
- Property details remained grounded in retrieved documents.
- Unknown questions resulted in safe refusal responses.
- Retrieval quality was consistent across brochures, FAQs and guides.

---

### Limitations

- External real estate projects are not included.
- Knowledge is limited to the supplied company documents.
- Retrieval quality depends on the completeness of the knowledge base.

---

## Conclusion

The hallucination evaluation demonstrates that the retrieval-augmented generation (RAG) pipeline produces reliable and grounded responses.

Across twenty evaluation questions:

- 90% of the questions were answered using retrieved evidence.
- 10% resulted in correct refusals due to missing knowledge.
- No hallucinated responses were observed.

This indicates that the system prioritizes factual accuracy over unsupported generation, making it suitable for real estate question answering where trustworthy information is essential.
