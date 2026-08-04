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
