# Implementation Tasks

---

# Part 1 — Relationship Discovery

Before writing the queries, I identified the primary and foreign keys of the tables and examined their relationships using the ER diagram generated in pgAdmin 4.

## Primary Keys (PK)

| Table | Primary Key |
|-------|-------------|
| country | `country_id` |
| city | `city_id` |
| language | `language_id` |
| actor | `actor_id` |
| address | `address_id` |
| category | `category_id` |
| film | `film_id` |
| customer | `customer_id` |
| staff | `staff_id` |
| film_actor | (`actor_id`, `film_id`) *(Composite Primary Key)* |
| film_category | (`film_id`, `category_id`) *(Composite Primary Key)* |
| inventory | `inventory_id` |
| rental | `rental_id` |
| store | `store_id` |
| payment | `payment_id` |

---

## Foreign Keys (FK)

| Table | Foreign Key(s) |
|-------|----------------|
| country | None |
| city | `country_id` |
| language | None |
| actor | None |
| address | `city_id` |
| category | None |
| film | `language_id` |
| customer | `address_id` |
| staff | `address_id` |
| film_actor | `actor_id`, `film_id` |
| film_category | `film_id`, `category_id` |
| inventory | `film_id`, `store_id` |
| rental | `inventory_id`, `customer_id`, `staff_id` |
| store | `manager_id`, `address_id` |
| payment | `customer_id`, `staff_id`, `rental_id` |

---

## Relationship Diagram

I generated the Entity Relationship (ER) Diagram using **pgAdmin 4** and have attached it in the submission.

---

# Part 2 — SQL JOIN Challenges

1. Display Customer Name, Email, City, and Country.
2. Display every payment with Customer Name, Film Title, and Amount Paid.
3. Display every payment with Customer Name, Film Title, and Amount Paid.
4. Find the Top 10 customers based on total amount spent.
5. Display each film with its Category and Rental Rate.
6. Find all actors who appeared in each film.
7. Count how many films belong to each category.
8. Determine which categories generated the highest revenue.
9. Find customers who have rented more than 20 films.
10. Determine which cities generated the highest rental revenue.

---

# Bonus Challenge

Without looking at any online solution, determine the shortest path of table joins needed to answer the following question:

> **Which actor has generated the highest total rental revenue?**

Since there is no direct relationship between the `actor` and `payment` tables, the required intermediate tables must first be identified before writing the SQL query.

---

# JOINs Used

## INNER JOIN

I used `INNER JOIN` throughout this assignment because each business question required only matching records between related tables. `INNER JOIN` returns rows only when a matching value exists in both tables, making it the most appropriate join type for these queries.

The following relationships were used:

- `customer` → `address`
- `address` → `city`
- `city` → `country`
- `customer` → `payment`
- `payment` → `rental`
- `rental` → `inventory`
- `inventory` → `film`
- `film` → `film_category`
- `film_category` → `category`
- `film` → `film_actor`
- `film_actor` → `actor`

These joins allowed information stored across multiple normalized tables to be combined into meaningful business reports.

---

# Business Insights

1. **Customer spending is highly concentrated among a few customers.**  
   Eleanor Hunt was the highest-spending customer with a total of **$211.55**, followed closely by Karl Seal with **$208.58**. This suggests that a relatively small group of loyal customers contributes a significant portion of the rental revenue.

2. **The Sports category generated the highest rental revenue.**  
   Although the Sports category contains **74 films**, it also generated the highest total revenue (**$4892.19**), making it the most profitable category in the DVD rental business. Sci-Fi and Animation were the next highest revenue-generating categories.

3. **Actor popularity directly impacts revenue generation.**  
   Gina Degeneres generated the highest total rental revenue (**$3129.17**) among all actors, indicating that films featuring certain actors tend to attract more rentals and contribute more to the company's overall revenue.

---
