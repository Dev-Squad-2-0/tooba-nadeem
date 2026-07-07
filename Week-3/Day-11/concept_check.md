## Concept Check

### 1. Why do relational databases split data into multiple tables?

Relational databases split data into multiple tables to:
- reduce duplicate data
- save storage
- maintain consistency

Each table stores information about one entity (such as customers or films).
Relationships between tables are created using keys.

### 2. Difference between INNER JOIN and LEFT JOIN

- **INNER JOIN** returns only the rows that have matching values in both tables.
- **LEFT JOIN** returns all rows from the left table and the matching rows from the right table. If there is no match, the right table's columns contain `NULL`.

### 3. When would you use a FULL OUTER JOIN?

A **FULL OUTER JOIN** is used when you want to include all records from both tables, whether they have matching values or not. Unmatched rows from either table will contain `NULL` for the missing columns.

### 4. Why are Primary Keys and Foreign Keys important?

- A **Primary Key** uniquely identifies each record in a table.
- A **Foreign Key** links one table to another by referencing the primary key of another table.

Together, they maintain relationships between tables and ensure data integrity.

### 5. Explain normalization in simple words.

Normalization is the process of organizing a database by storing related information in separate tables instead of repeating the same data. This reduces redundancy, saves storage space, and makes the database easier to maintain.

### 6. What is an ER Diagram?

An **Entity Relationship (ER) Diagram** is a visual representation of a database. It shows the tables (entities), their primary and foreign keys, and how the tables are related to each other.

### 7. What happens if a JOIN condition is incorrect?

If a JOIN condition is incorrect, SQL may return incorrect or duplicate results, miss matching records, or produce a large number of unrelated rows (called a Cartesian product). Therefore, it is important to join tables using the correct primary and foreign key relationships.
