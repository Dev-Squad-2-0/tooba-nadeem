-- just discovered we can comment/uncomment in Postgres using: "cntrl+/"
-- Implementation Task
-- Part 1 — Aggregation Basics
--1. Find the total revenue generated per store.
SELECT 
	i.store_id, 
	SUM(p.amount) AS revenue
FROM payment AS p
JOIN rental as r
	ON p.rental_id=r.rental_id
JOIN inventory AS i
	ON r.inventory_id=i.inventory_id
GROUP BY i.store_id;

--2. Find the average rental duration per film category.
SELECT c.name as category, ROUND(AVG(f.rental_duration),2) AS average_rental_duration
FROM film AS f
JOIN film_category AS fc
	ON f.film_id=fc.film_id
JOIN category AS c
	ON fc.category_id = c.category_id
GROUP BY c.name;

--3. Find the number of rentals made each month.
SELECT 
	EXTRACT(MONTH FROM rental_date) AS month, 
	COUNT(*) AS number_of_rentals
FROM rental
GROUP BY month
ORDER BY month;

--4. Find categories with more than 50 films (use HAVING).
SELECT 
	c.name as category, 
	COUNT(fc.film_id) AS number_of_films
FROM film_category AS fc
	JOIN category AS c
ON fc.category_id = c.category_id
GROUP BY c.name
HAVING COUNT(fc.film_id)> 50
ORDER BY category;

-- Part 2 — Subquery Challenges
-- 5. Find customers who spent more than the average customer spend.
SELECT
    c.first_name,
    c.last_name,
    SUM(p.amount) AS money_spent
FROM customer AS c
JOIN payment AS p
    ON c.customer_id = p.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
HAVING SUM(p.amount) >
(
    SELECT AVG(customer_total)
    FROM
    (
        SELECT
            customer_id,
            SUM(amount) AS customer_total
        FROM payment
        GROUP BY customer_id
    ) AS totals
);

-- 6. Find the film(s) with the highest rental rate in each category (use a correlated subquery).
SELECT
    c.name AS category,
    f.title,
    f.rental_rate
FROM film AS f
JOIN film_category AS fc
    ON f.film_id = fc.film_id
JOIN category AS c
    ON fc.category_id = c.category_id
WHERE f.rental_rate =
(
    SELECT MAX(f2.rental_rate)
    FROM film AS f2
    JOIN film_category AS fc2
        ON f2.film_id = fc2.film_id
    WHERE fc2.category_id = fc.category_id
)
ORDER BY c.name, f.title;


-- 7. Find customers who have never rented a film (use NOT IN / NOT EXISTS).
SELECT c.first_name, c.last_name
FROM customer AS c
WHERE NOT EXISTS
(SELECT 1
FROM rental AS r
WHERE r.customer_id=c.customer_id);

-- 8. Find the store with the highest total revenue using a subquery in the WHERE clause.
SELECT
    i.store_id,
    SUM(p.amount) AS total_revenue
FROM payment AS p
JOIN rental AS r
    ON p.rental_id = r.rental_id
JOIN inventory AS i
    ON r.inventory_id = i.inventory_id
GROUP BY i.store_id
HAVING SUM(p.amount) =
(
    SELECT MAX(store_revenue)
    FROM
    (
        SELECT
            i.store_id,
            SUM(p.amount) AS store_revenue
        FROM payment AS p
        JOIN rental AS r
            ON p.rental_id = r.rental_id
        JOIN inventory AS i
            ON r.inventory_id = i.inventory_id
        GROUP BY i.store_id
    ) AS revenue
);

-- Part 3 — CTE & Window Function Challenges
-- 9. Using a CTE, rank customers by total spend within each city.
WITH customer_spending AS
(
    SELECT
        ci.city,
        c.customer_id,
        c.first_name,
        c.last_name,
        SUM(p.amount) AS total_spent
    FROM customer AS c
    JOIN address AS a
        ON c.address_id = a.address_id
    JOIN city AS ci
        ON a.city_id = ci.city_id
    JOIN payment AS p
        ON c.customer_id = p.customer_id
    GROUP BY
        ci.city,
        c.customer_id,
        c.first_name,
        c.last_name
)

SELECT
    city,
    first_name,
    last_name,
    total_spent,
    RANK() OVER
    (
        PARTITION BY city
        ORDER BY total_spent DESC
    ) AS city_rank
FROM customer_spending
ORDER BY city, city_rank;


-- 10. Using ROW_NUMBER(), find the most recently rented film for each customer.
WITH recent_rentals AS
(
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        f.title,
        r.rental_date,
        ROW_NUMBER() OVER
        (
            PARTITION BY c.customer_id
            ORDER BY r.rental_date DESC
        ) AS rn
    FROM customer AS c
    JOIN rental AS r
        ON c.customer_id = r.customer_id
    JOIN inventory AS i
        ON r.inventory_id = i.inventory_id
    JOIN film AS f
        ON i.film_id = f.film_id
)

SELECT
    customer_id,
    first_name,
    last_name,
    title,
    rental_date
FROM recent_rentals
WHERE rn = 1
ORDER BY customer_id;

-- 11. Using a CTE, calculate month-over-month rental revenue growth.
WITH monthly_revenue AS
(
    SELECT
        DATE_TRUNC('month', payment_date) AS month,
        SUM(amount) AS revenue
    FROM payment
    GROUP BY DATE_TRUNC('month', payment_date)
)

SELECT
    month,
    revenue,
    LAG(revenue) OVER
    (
        ORDER BY month
    ) AS previous_month,
    ROUND(
        (
            (revenue - LAG(revenue) OVER (ORDER BY month))
            /
            LAG(revenue) OVER (ORDER BY month)
        ) * 100,
        2
    ) AS growth_percent
FROM monthly_revenue
ORDER BY month;


-- 12. Find the top 3 highest-grossing films per category using RANK() inside a CTE.
WITH film_revenue AS
(
    SELECT
        c.name AS category,
        f.title,
        SUM(p.amount) AS revenue
    FROM payment AS p
    JOIN rental AS r
        ON p.rental_id = r.rental_id
    JOIN inventory AS i
        ON r.inventory_id = i.inventory_id
    JOIN film AS f
        ON i.film_id = f.film_id
    JOIN film_category AS fc
        ON f.film_id = fc.film_id
    JOIN category AS c
        ON fc.category_id = c.category_id
    GROUP BY
        c.name,
        f.title
),

ranked_films AS
(
    SELECT
        *,
        RANK() OVER
        (
            PARTITION BY category
            ORDER BY revenue DESC
        ) AS film_rank
    FROM film_revenue
)

SELECT
    category,
    title,
    revenue,
    film_rank
FROM ranked_films
WHERE film_rank <= 3
ORDER BY category, film_rank;


-- Bonus Challenge
-- Without looking at any online solution, write a single query (using CTEs) that finds: Which staff member processed the highest revenue in each store, and what percentage of that store's total revenue did they contribute? This requires combining aggregation, a CTE, and a percentage calculation in the same query.
WITH staff_revenue AS
(
    SELECT
        s.store_id,
        st.staff_id,
        st.first_name,
        st.last_name,
        SUM(p.amount) AS staff_total
    FROM payment AS p
    JOIN staff AS st
        ON p.staff_id = st.staff_id
    JOIN store AS s
        ON st.store_id = s.store_id
    GROUP BY
        s.store_id,
        st.staff_id,
        st.first_name,
        st.last_name
),

store_totals AS
(
    SELECT
        store_id,
        SUM(staff_total) AS store_total
    FROM staff_revenue
    GROUP BY store_id
),

ranked_staff AS
(
    SELECT
        sr.*,
        st.store_total,
        RANK() OVER
        (
            PARTITION BY sr.store_id
            ORDER BY sr.staff_total DESC
        ) AS staff_rank
    FROM staff_revenue AS sr
    JOIN store_totals AS st
        ON sr.store_id = st.store_id
)

SELECT
    store_id,
    first_name,
    last_name,
    staff_total,
    store_total,
    ROUND((staff_total / store_total) * 100, 2) AS revenue_percentage
FROM ranked_staff
WHERE staff_rank = 1
ORDER BY store_id;
