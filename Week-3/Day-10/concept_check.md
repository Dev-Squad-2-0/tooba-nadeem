# Concept Check

## 1. What problem does SQL solve that CSV files cannot?

- SQL allows users to efficiently store, manage, and query large amounts of data without loading the entire dataset into memory.
- It also supports multiple users accessing the data simultaneously and maintains relationships between different tables, which CSV files cannot do.

---

## 2. What is the difference between a database table and a spreadsheet?

- A database table stores data in rows and columns inside a database and is designed for efficient storage, querying, and relationships with other tables.
- A spreadsheet also stores data in rows and columns but is mainly used for manual data entry, calculations, and smaller datasets.

---

## 3. What is a Primary Key?

- A Primary Key is a column (or a combination of columns) that uniquely identifies each row in a table. 
- It cannot contain duplicate or `NULL` values.

---

## 4. What is a Foreign Key?

- A Foreign Key is a column in one table that references the Primary Key of another table.
- It creates a relationship between two tables and helps maintain data integrity.

---

## 5. What is the difference between `WHERE` and `HAVING`?

- `WHERE` filters individual rows **before** grouping.
- `HAVING` filters grouped data **after** the `GROUP BY` operation.

---

## 6. What is the difference between `ORDER BY` and `GROUP BY`?

- `ORDER BY` sorts the query results in ascending or descending order.
- `GROUP BY` groups rows with the same values together so aggregate functions can be applied.

---

## 7. What does `DISTINCT` do?

`DISTINCT` removes duplicate values from the query result and returns only unique values.

---

## 8. When should you use `LIMIT`?

`LIMIT` is used when you want to return only a specified number of rows from a query. It is useful for previewing data or retrieving only the required records.

---

## 9. What are aggregate functions?

Aggregate functions perform calculations on multiple rows and return a single result. Common aggregate functions include:

- `COUNT()`
- `SUM()`
- `AVG()`
- `MIN()`
- `MAX()`

---

## 10. Why do Data Scientists prefer databases over Excel for large datasets?

Data Scientists prefer databases because they can:

- efficiently store and query millions of records
- support multiple users
- maintain relationships between tables
- ensure data integrity
- scale much better than Excel for large datasets
