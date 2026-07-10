# 02 - Database Exploration

## Objective

The first step of the project was to explore the AdventureWorks database to understand its structure, business domains, and relationships between entities. This exploration was necessary to design a reusable analytics layer that minimizes repeated queries on the operational database.

---

# Database Overview

AdventureWorks is a transactional database that simulates the operations of a manufacturing and retail company. It contains data related to customers, products, sales, employees, purchasing, vendors, inventory, and territories.

The database is organized into multiple schemas, where each schema represents a specific business area.

---

# Schemas Explored

During the exploration phase, the following schemas were examined:

| Schema | Description |
|---------|-------------|
| Sales | Customer orders, sales transactions, sales territories, and salespeople. |
| Production | Products, categories, inventory, product models, and manufacturing information. |
| Purchasing | Vendors, purchase orders, and supplier-related information. |
| HumanResources | Employee records and organizational information. |
| Person | Customer and employee personal details, addresses, and contact information. |

Some schemas contain mostly **views** instead of physical tables. This is expected in the AdventureWorks database, where certain schemas expose pre-defined business representations instead of storing raw data directly.

---

# Business Domains Selected

Based on the database exploration, six major business domains were selected for the analytics layer.

1. Customer Analytics
2. Product Analytics
3. Sales Analytics
4. Employee Analytics
5. Territory Analytics
6. Inventory & Purchasing Analytics

These domains satisfy the project requirement of using data from at least five different business areas while covering the core operations of the business.

---

# Analytics Layer Design

Instead of querying the operational database repeatedly, an intermediate analytics layer was designed.

The analytics layer follows a layered architecture where each analytical object builds upon previously created objects rather than recalculating the same metrics multiple times.

The design consists of four logical layers:

## Layer 1 - Base Views

These views combine frequently joined operational tables into reusable datasets.

Examples include:

- Customer Base
- Product Base
- Employee Base
- Order Base
- Territory Base
- Inventory Base

These views act as the foundation for all later analytical objects.

---

## Layer 2 - Materialized Metrics

This layer performs expensive business calculations such as:

- Revenue
- Sales totals
- Customer spending
- Product performance
- Employee performance
- Territory performance
- Inventory metrics

Since these calculations involve multiple joins and aggregations, they are implemented as **Materialized Views** to avoid recalculating the same metrics repeatedly.

---

## Layer 3 - Analytical Views

This layer creates higher-level business insights from the aggregated metrics.

Examples include:

- Customer Segments
- Product Rankings
- Employee Rankings
- Territory Rankings
- Vendor Rankings

These analytical views reuse the results from Layer 2 instead of accessing the operational tables directly.

---

## Layer 4 - Executive KPI Summary

The final layer provides a single reusable dataset containing executive-level KPIs for reporting and dashboarding.

This serves as the primary data source for notebooks, dashboards, and business reports.

---

# Why Views Instead of Tables?

The project requirements specify the creation of reusable analytical **tables or views**. After evaluating both approaches, views and materialized views were chosen instead of physical tables.

### Reasons for using Views

- Views always reflect the latest data from the operational database.
- They eliminate the need to duplicate data.
- They simplify maintenance by storing only the query definition.
- They provide reusable datasets that can be referenced throughout the analytics pipeline.

### Reasons for using Materialized Views

- Materialized views store the results of computationally expensive queries.
- They improve performance for aggregations involving multiple joins and large datasets.
- They reduce repeated calculations when the same analytical metrics are accessed multiple times.
- They can be refreshed whenever updated analytical data is required.

### Why Physical Tables Were Not Used

Physical analytical tables require an ETL or refresh process to keep the stored data synchronized with the operational database.

Since the objective of this project is to build a reusable analytics layer rather than a full data warehouse, creating physical tables would introduce unnecessary data duplication and maintenance overhead.

Using views and materialized views provides a cleaner, more maintainable architecture while fully satisfying the project requirements.

---

# Planned Analytical Objects

| Layer | Object | Type |
|--------|-----------------------|-------------------|
| Layer 1 | customer_base | View |
| Layer 1 | product_base | View |
| Layer 1 | employee_base | View |
| Layer 1 | order_base | View |
| Layer 1 | territory_base | View |
| Layer 1 | inventory_base | View |
| Layer 2 | customer_metrics | Materialized View |
| Layer 2 | product_metrics | Materialized View |
| Layer 2 | employee_metrics | Materialized View |
| Layer 2 | territory_metrics | Materialized View |
| Layer 2 | monthly_revenue | Materialized View |
| Layer 2 | inventory_metrics | Materialized View |
| Layer 3 | customer_segments | View |
| Layer 3 | product_rankings | View |
| Layer 3 | employee_rankings | View |
| Layer 3 | territory_rankings | View |
| Layer 3 | vendor_rankings | View |
| Layer 4 | exec_kpi_summary | Materialized View |

---

# Summary

The database exploration identified the key business domains and relationships required for the analytics layer. A layered architecture based on reusable views and materialized views was selected to improve maintainability, reduce redundant calculations, and support efficient business reporting while keeping the operational database isolated from repeated analytical queries.
