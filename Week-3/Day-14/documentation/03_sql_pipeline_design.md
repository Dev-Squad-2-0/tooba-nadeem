# 03 - SQL Pipeline Design

## Objective

The objective of the SQL pipeline is to create a reusable analytics layer that separates analytical reporting from the operational AdventureWorks database.

Instead of repeatedly querying transactional tables, the pipeline transforms raw operational data into reusable analytical objects that can support dashboards, executive reports, and future analytical tasks.

---

# Pipeline Architecture

The analytics pipeline follows a layered architecture.

Each layer builds upon the previous one, ensuring that calculations are performed only once and reused throughout the project.

```
Operational Database
        │
        ▼
Layer 1
Base Views
        │
        ▼
Layer 2
Materialized Metric Views
        │
        ▼
Layer 3
Analytical Views
        │
        ▼
Layer 4
Executive KPI Summary
```

This design minimizes redundant calculations while improving readability, maintainability, and performance.

---

# Layer 1 – Base Views

The first layer creates reusable views by combining frequently joined operational tables.

These views provide a clean business-oriented representation of the data without modifying or duplicating the original tables.

### Base Views Created

- customer_base
- product_base
- employee_base
- order_base
- territory_base
- inventory_base

These views hide complex joins and become reusable building blocks for all downstream analytics.

---

# Layer 2 – Materialized Metrics

The second layer performs computationally expensive business calculations.

Instead of recalculating aggregates every time a report is executed, these results are stored inside materialized views.

### Materialized Views Created

- customer_metrics
- product_metrics
- employee_metrics
- territory_metrics
- monthly_revenue
- inventory_metrics

Examples of calculated metrics include:

- Total Sales
- Revenue
- Order Counts
- Average Order Value
- Units Sold
- Inventory Status
- Territory Performance
- Employee Sales

Materialized views significantly reduce execution time for frequently accessed analytical queries.

---

# Layer 3 – Analytical Views

The third layer derives business insights from the aggregated metrics created in Layer 2.

Instead of querying operational tables, these views reuse the materialized metrics to generate analytical outputs.

Examples include:

- Customer Segmentation
- Product Rankings
- Employee Rankings
- Territory Rankings
- Vendor Rankings

Since these views operate on already aggregated data, they remain lightweight and easy to maintain.

---

# Layer 4 – Executive KPI Summary

The final layer combines key business indicators into a single executive reporting dataset.

This layer acts as the primary source for dashboards, visualizations, and executive reporting.

Typical KPIs include:

- Total Revenue
- Total Orders
- Total Customers
- Total Products Sold
- Employee Performance
- Territory Performance
- Inventory Health

This design allows business users to access high-level metrics without interacting with the transactional database.

---

# Dependency Flow

The pipeline was designed so that every analytical object builds upon previous objects whenever possible.

```
Operational Tables
        │
        ▼
customer_base
product_base
employee_base
order_base
territory_base
inventory_base
        │
        ▼
customer_metrics
product_metrics
employee_metrics
territory_metrics
monthly_revenue
inventory_metrics
        │
        ▼
customer_segments
product_rankings
employee_rankings
territory_rankings
vendor_rankings
        │
        ▼
exec_kpi_summary
```

This layered dependency avoids recalculating the same joins and aggregations multiple times.

---

# Why Materialized Views Were Used

Some analytical queries involve multiple joins and aggregation operations over large transactional tables.

Examples include:

- Revenue calculations
- Customer purchase history
- Product sales summaries
- Territory performance
- Monthly sales analysis

Executing these calculations repeatedly would increase query execution time.

Materialized views store the computed results physically and can be refreshed whenever updated data is required.

This approach improves performance while keeping the analytics layer reusable.

---

# Refresh Strategy

Whenever the operational database is updated, the materialized views can be refreshed using:

```sql
REFRESH MATERIALIZED VIEW analytics.customer_metrics;
REFRESH MATERIALIZED VIEW analytics.product_metrics;
REFRESH MATERIALIZED VIEW analytics.employee_metrics;
REFRESH MATERIALIZED VIEW analytics.territory_metrics;
REFRESH MATERIALIZED VIEW analytics.monthly_revenue;
REFRESH MATERIALIZED VIEW analytics.inventory_metrics;
```

Refreshing updates the stored analytical metrics without recreating the views.

---

# Design Principles Followed

The analytics layer was designed according to the following principles:

- Reuse existing analytical objects whenever possible.
- Avoid repeated joins on operational tables.
- Avoid recalculating identical business metrics.
- Separate transactional processing from analytical reporting.
- Keep the SQL pipeline modular and maintainable.
- Improve performance using materialized views for expensive aggregations.
- Create a scalable foundation for dashboards and future analytical tasks.

---

# Benefits of the Pipeline

The implemented SQL pipeline provides several advantages:

- Cleaner SQL organization through layered design.
- Reduced query complexity.
- Improved execution performance.
- Centralized business metrics.
- Easier maintenance and debugging.
- Reusable datasets for notebooks, dashboards, and reports.
- Reduced load on the operational AdventureWorks database.

---

# Summary

A layered SQL pipeline was implemented to transform raw operational data into reusable analytical datasets.

The pipeline begins with reusable base views, computes business metrics using materialized views, derives higher-level analytical insights, and finally produces executive KPIs for reporting.

This architecture satisfies the hackathon requirement of building a reusable analytics layer while minimizing redundant calculations and improving analytical performance.
