# Concept Check

## 1. Why are multiple CTEs preferred over one large nested query?

Multiple CTEs make the query easier to read, understand, and debug. Each CTE performs one specific task, so the SQL is more organized and calculations can be reused without repeating code.

---

## 2. When would you use a window function instead of GROUP BY?

Use a window function when you want to perform calculations (such as ranking or running totals) **without reducing the number of rows**. `GROUP BY` combines rows into groups, while window functions keep every row in the result.

---

## 3. Explain the difference between `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`.

- **ROW_NUMBER()** gives every row a unique number, even if values are tied.
- **RANK()** gives the same rank to tied values but skips the next rank.
- **DENSE_RANK()** also gives the same rank to tied values but does **not** skip any ranks.

Example:

| Score | ROW_NUMBER | RANK | DENSE_RANK |
|-------|-----------:|-----:|-----------:|
| 100 | 1 | 1 | 1 |
| 100 | 2 | 1 | 1 |
| 90 | 3 | 3 | 2 |

---

## 4. What is conditional aggregation?

Conditional aggregation is calculating values only for rows that meet a certain condition, usually by using `CASE WHEN` inside aggregate functions like `SUM()` or `COUNT()`.

Example:

```sql
SUM(CASE WHEN segment = 'Gold' THEN total_spent ELSE 0 END)
```

This calculates the total spending of only Gold customers.

---

## 5. How does `CASE WHEN` improve analytical reporting?

`CASE WHEN` allows you to categorize or label data based on conditions. It helps create business-friendly reports, such as customer segments, sales categories, or performance levels.

---

## 6. Why should SQL queries be broken into logical stages?

Breaking a query into logical stages makes it easier to understand, test, and maintain. It also allows intermediate results to be reused instead of calculating the same values multiple times.

---

## 7. What makes a SQL query maintainable?

A maintainable SQL query is:
- Easy to read with clear formatting.
- Organized into logical steps using CTEs.
- Well-commented.
- Avoids repeating calculations.
- Uses meaningful table and column aliases.
