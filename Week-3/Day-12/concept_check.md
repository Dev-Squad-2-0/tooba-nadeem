# Concept Check

## 1. What is the difference between `WHERE` and `HAVING`?

- `WHERE` filters individual rows **before** grouping and aggregation.
- `HAVING` filters grouped results **after** `GROUP BY` and aggregate functions have been applied.

---

## 2. When would you use a correlated subquery instead of a `JOIN`?

A correlated subquery is used when the inner query depends on each row of the outer query. It is useful for comparing each row to a value calculated from its own group, such as finding the highest rental rate within each film category.

---

## 3. What is a CTE, and why is it more readable than a nested subquery?

A **Common Table Expression (CTE)** is a temporary named result set created using the `WITH` clause. It makes complex queries easier to read, understand, and maintain by breaking them into smaller, logical steps instead of nesting multiple subqueries.

---

## 4. Explain the difference between `RANK()` and `DENSE_RANK()`.

Both functions assign rankings while handling ties differently.

Example values:

| Score | `RANK()` | `DENSE_RANK()` |
|--------|---------:|---------------:|
| 100 | 1 | 1 |
| 95 | 2 | 2 |
| 95 | 2 | 2 |
| 90 | 4 | 3 |

- `RANK()` leaves gaps after ties.
- `DENSE_RANK()` does not leave gaps.

---

## 5. What does `PARTITION BY` do differently from `GROUP BY`?

- `GROUP BY` combines rows into groups and returns one row for each group.
- `PARTITION BY` keeps all rows but performs calculations separately within each partition, making it useful for window functions.

---

## 6. Can a subquery return multiple rows? What operator would you use in that case?

Yes. A subquery can return multiple rows. In that case, operators such as `IN`, `ANY`, or `ALL` are commonly used, depending on the comparison being made.

---

## 7. Give an example of when `CASE WHEN` is useful inside an aggregate function.

`CASE WHEN` is useful for conditional aggregation. For example, it can count only rentals that meet a condition or calculate the total revenue for a specific film rating while ignoring all others.# Concept Check

## 1. What is the difference between `WHERE` and `HAVING`?

- `WHERE` filters individual rows **before** grouping and aggregation.
- `HAVING` filters grouped results **after** `GROUP BY` and aggregate functions have been applied.

---

## 2. When would you use a correlated subquery instead of a `JOIN`?

A correlated subquery is used when the inner query depends on each row of the outer query. It is useful for comparing each row to a value calculated from its own group, such as finding the highest rental rate within each film category.

---

## 3. What is a CTE, and why is it more readable than a nested subquery?

A **Common Table Expression (CTE)** is a temporary named result set created using the `WITH` clause. It makes complex queries easier to read, understand, and maintain by breaking them into smaller, logical steps instead of nesting multiple subqueries.

---

## 4. Explain the difference between `RANK()` and `DENSE_RANK()`.

Both functions assign rankings while handling ties differently.

Example values:

| Score | `RANK()` | `DENSE_RANK()` |
|--------|---------:|---------------:|
| 100 | 1 | 1 |
| 95 | 2 | 2 |
| 95 | 2 | 2 |
| 90 | 4 | 3 |

- `RANK()` leaves gaps after ties.
- `DENSE_RANK()` does not leave gaps.

---

## 5. What does `PARTITION BY` do differently from `GROUP BY`?

- `GROUP BY` combines rows into groups and returns one row for each group.
- `PARTITION BY` keeps all rows but performs calculations separately within each partition, making it useful for window functions.

---

## 6. Can a subquery return multiple rows? What operator would you use in that case?

Yes. A subquery can return multiple rows. In that case, operators such as `IN`, `ANY`, or `ALL` are commonly used, depending on the comparison being made.

---

## 7. Give an example of when `CASE WHEN` is useful inside an aggregate function.

`CASE WHEN` is useful for conditional aggregation. For example, it can count only rentals that meet a condition or calculate the total revenue for a specific film rating while ignoring all others.
