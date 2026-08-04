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
|----------|-------------|
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


## Day2 Task2 Evaluation – Chunk Size Comparison

To determine the most effective document chunking strategy for the RAG pipeline, three different chunk configurations were evaluated. Each configuration was tested by rebuilding the vector database and querying the system with the same set of property-related questions.

### Chunk Size Comparison

| Chunk Size | Overlap | Chunks Created | Retrieval Quality | Observations |
|------------|---------|---------------:|-------------------|--------------|
| 300 | 50 | 322 | Low | Context became fragmented, duplicate chunks appeared, and some relevant projects were not retrieved. |
| 600 | 100 | 136 | Medium | Reduced fragmentation compared to 300, but retrieval quality remained similar and duplicate results were still present. |
| 1000 | 200 | 77 | High | Preserved complete project context, retrieved all relevant Lahore projects, and produced the most relevant search results. |

### Observations

- Smaller chunk sizes produced significantly more document chunks, increasing fragmentation and reducing retrieval quality.
- Larger chunks preserved semantic context more effectively, resulting in more complete and relevant search results.
- Duplicate retrievals were observed across all configurations because overlapping chunks from the same document were considered relevant by the vector database.
- The largest chunk size provided the best balance between retrieval quality and database size.

### Final Configuration

The final RAG pipeline uses:

- **Chunk Size:** `1000`
- **Chunk Overlap:** `200`

This configuration was selected because it consistently returned the most relevant property information while preserving complete project descriptions and reducing unnecessary document fragmentation.

### Notes

The vector database is persisted locally using ChromaDB. On subsequent runs, the existing vector database is loaded instead of rebuilding embeddings, which significantly reduces startup time. The database is only rebuilt when the knowledge base changes.


## Day2 Task3 – Structured Retrieval (SQL + Semantic Search)

### Objective

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
