-- 1.Display Customer Name, Email, City, and Country.
SELECT
    cu.first_name,
    cu.last_name,
    cu.email,
    ci.city,
    co.country
FROM customer AS cu
INNER JOIN address AS ad
    ON cu.address_id = ad.address_id
INNER JOIN city AS ci
    ON ad.city_id = ci.city_id
INNER JOIN country AS co
    ON ci.country_id = co.country_id;


-- 2. Display every payment with Customer Name, Film Title, and Amount Paid.
SELECT
    c.first_name,
    c.last_name,
    f.title AS film_title,
    p.amount
FROM payment AS p
INNER JOIN customer AS c
    ON p.customer_id = c.customer_id
INNER JOIN rental AS r
    ON p.rental_id = r.rental_id
INNER JOIN inventory AS i
    ON r.inventory_id = i.inventory_id
INNER JOIN film AS f
    ON i.film_id = f.film_id;

-- 3. Display every payment with Customer Name, Film Title, and Amount Paid.
SELECT
    c.first_name,
    c.last_name,
    f.title AS film_title,
    p.amount
FROM payment AS p
INNER JOIN customer AS c
    ON p.customer_id = c.customer_id
INNER JOIN rental AS r
    ON p.rental_id = r.rental_id
INNER JOIN inventory AS i
    ON r.inventory_id = i.inventory_id
INNER JOIN film AS f
    ON i.film_id = f.film_id;

-- 4. Find the Top 10 customers based on total amount spent.
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(p.amount) AS total_spent
FROM customer AS c
INNER JOIN payment AS p
    ON c.customer_id = p.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
ORDER BY total_spent DESC
LIMIT 10;

-- 5. Display each film with its Category and Rental Rate.
SELECT
    f.title AS film_title,
    c.name AS category,
    f.rental_rate
FROM film AS f
INNER JOIN film_category AS fc
    ON f.film_id = fc.film_id
INNER JOIN category AS c
    ON fc.category_id = c.category_id
ORDER BY f.title;

-- 6. Find all actors who appeared in each film.
SELECT
    f.title AS film_title,
    a.first_name,
    a.last_name
FROM film AS f
INNER JOIN film_actor AS fa
    ON f.film_id = fa.film_id
INNER JOIN actor AS a
    ON fa.actor_id = a.actor_id
ORDER BY
    f.title,
    a.last_name,
    a.first_name;

-- 7. Count how many films belong to each category.
SELECT
    c.name AS category,
    COUNT(f.film_id) AS total_films
FROM category AS c
INNER JOIN film_category AS fc
    ON c.category_id = fc.category_id
INNER JOIN film AS f
    ON fc.film_id = f.film_id
GROUP BY
    c.category_id,
    c.name
ORDER BY
    total_films DESC;

-- 8. Which categories generated the highest revenue?
SELECT
    c.name AS category,
    SUM(p.amount) AS total_revenue
FROM category AS c
INNER JOIN film_category AS fc
    ON c.category_id = fc.category_id
INNER JOIN film AS f
    ON fc.film_id = f.film_id
INNER JOIN inventory AS i
    ON f.film_id = i.film_id
INNER JOIN rental AS r
    ON i.inventory_id = r.inventory_id
INNER JOIN payment AS p
    ON r.rental_id = p.rental_id
GROUP BY
    c.category_id,
    c.name
ORDER BY
    total_revenue DESC;

-- 9. Find customers who have rented more than 20 films.
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(r.rental_id) AS total_rentals
FROM customer AS c
INNER JOIN rental AS r
    ON c.customer_id = r.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name
HAVING
    COUNT(r.rental_id) > 20
ORDER BY
    total_rentals DESC;

-- 10. Which cities generated the highest rental revenue?
SELECT
    ci.city,
    SUM(p.amount) AS total_revenue
FROM payment AS p
INNER JOIN customer AS c
    ON p.customer_id = c.customer_id
INNER JOIN address AS a
    ON c.address_id = a.address_id
INNER JOIN city AS ci
    ON a.city_id = ci.city_id
GROUP BY
    ci.city_id,
    ci.city
ORDER BY
    total_revenue DESC;

-- Bonus Challenge
-- Which actor has generated the highest total rental revenue?
SELECT
    a.actor_id,
    a.first_name,
    a.last_name,
    SUM(p.amount) AS total_revenue
FROM actor AS a
INNER JOIN film_actor AS fa
    ON a.actor_id = fa.actor_id
INNER JOIN film AS f
    ON fa.film_id = f.film_id
INNER JOIN inventory AS i
    ON f.film_id = i.film_id
INNER JOIN rental AS r
    ON i.inventory_id = r.inventory_id
INNER JOIN payment AS p
    ON r.rental_id = p.rental_id
GROUP BY
    a.actor_id,
    a.first_name,
    a.last_name
ORDER BY
    total_revenue DESC
LIMIT 1;