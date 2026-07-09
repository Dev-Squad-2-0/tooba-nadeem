------------------------------------------------------------
-- TASK 5: Executive Business Report
------------------------------------------------------------

-- 5a. Customer Segment Summary + Revenue by Segment
WITH customer_profile AS (
    SELECT
        c.customer_id, c.first_name, c.last_name, c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        COUNT(DISTINCT i.invoice_id) AS total_invoices,
        SUM(il.quantity) AS total_tracks,
        COUNT(DISTINCT g.genre_id) AS unique_genres,
        COUNT(DISTINCT ar.artist_id) AS unique_artists,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t ON il.track_id = t.track_id
    JOIN genre g ON t.genre_id = g.genre_id
    JOIN album al ON t.album_id = al.album_id
    JOIN artist ar ON al.artist_id = ar.artist_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),
customer_segments AS (
    SELECT *,
        CASE
            WHEN total_spent >= 40 AND total_invoices >= 7 AND unique_genres >= 5 THEN 'Platinum'
            WHEN total_spent >= 25 AND total_invoices >= 5 THEN 'Gold'
            WHEN total_spent >= 10 AND total_invoices >= 2 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM customer_profile
)
SELECT
    customer_segment,
    COUNT(*) AS customers,
    SUM(total_spent) AS revenue
FROM customer_segments
GROUP BY customer_segment;


-- 5b. Top Customer per Segment
WITH customer_profile AS (
    SELECT
        c.customer_id, c.first_name, c.last_name, c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        COUNT(DISTINCT i.invoice_id) AS total_invoices,
        SUM(il.quantity) AS total_tracks,
        COUNT(DISTINCT g.genre_id) AS unique_genres,
        COUNT(DISTINCT ar.artist_id) AS unique_artists,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t ON il.track_id = t.track_id
    JOIN genre g ON t.genre_id = g.genre_id
    JOIN album al ON t.album_id = al.album_id
    JOIN artist ar ON al.artist_id = ar.artist_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),
customer_segments AS (
    SELECT *,
        CASE
            WHEN total_spent >= 40 AND total_invoices >= 7 AND unique_genres >= 5 THEN 'Platinum'
            WHEN total_spent >= 25 AND total_invoices >= 5 THEN 'Gold'
            WHEN total_spent >= 10 AND total_invoices >= 2 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM customer_profile
)
SELECT customer_segment, customer_id, first_name, last_name, total_spent
FROM (
    SELECT
        customer_segment, customer_id, first_name, last_name, total_spent,
        ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY total_spent DESC) AS rn
    FROM customer_segments
) x
WHERE rn = 1;


-- 5c. Top Genre per Segment
WITH customer_profile AS (
    SELECT
        c.customer_id, c.first_name, c.last_name, c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        COUNT(DISTINCT i.invoice_id) AS total_invoices,
        SUM(il.quantity) AS total_tracks,
        COUNT(DISTINCT g.genre_id) AS unique_genres,
        COUNT(DISTINCT ar.artist_id) AS unique_artists,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t ON il.track_id = t.track_id
    JOIN genre g ON t.genre_id = g.genre_id
    JOIN album al ON t.album_id = al.album_id
    JOIN artist ar ON al.artist_id = ar.artist_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),
customer_segments AS (
    SELECT *,
        CASE
            WHEN total_spent >= 40 AND total_invoices >= 7 AND unique_genres >= 5 THEN 'Platinum'
            WHEN total_spent >= 25 AND total_invoices >= 5 THEN 'Gold'
            WHEN total_spent >= 10 AND total_invoices >= 2 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM customer_profile
),
genre_counts AS (
    SELECT c.customer_id, g.name AS genre, COUNT(*) AS purchases
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t ON il.track_id = t.track_id
    JOIN genre g ON t.genre_id = g.genre_id
    GROUP BY c.customer_id, g.name
),
favorite_genres AS (
    SELECT customer_id, genre, purchases
    FROM (
        SELECT customer_id, genre, purchases,
            ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY purchases DESC) AS rn
        FROM genre_counts
    ) x
    WHERE rn = 1
),
marketing_recommendation AS (
    SELECT cs.*, fg.genre,
        CASE
            WHEN cs.customer_segment = 'Platinum' THEN 'Early access to new releases'
            WHEN cs.customer_segment = 'Gold'     THEN 'Album bundle discounts'
            WHEN cs.customer_segment = 'Silver'   THEN 'Genre-based promotions'
            ELSE 'First purchase coupon'
        END AS campaign
    FROM customer_segments cs
    LEFT JOIN favorite_genres fg ON cs.customer_id = fg.customer_id
)
SELECT customer_segment, genre, customers
FROM (
    SELECT
        customer_segment, genre, COUNT(*) AS customers,
        ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY COUNT(*) DESC) AS rn
    FROM marketing_recommendation
    GROUP BY customer_segment, genre
) x
WHERE rn = 1;


-- 5d. Best Performing Country + Revenue Contribution by Country
WITH customer_profile AS (
    SELECT
        c.customer_id, c.first_name, c.last_name, c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        COUNT(DISTINCT i.invoice_id) AS total_invoices,
        SUM(il.quantity) AS total_tracks,
        COUNT(DISTINCT g.genre_id) AS unique_genres,
        COUNT(DISTINCT ar.artist_id) AS unique_artists,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t ON il.track_id = t.track_id
    JOIN genre g ON t.genre_id = g.genre_id
    JOIN album al ON t.album_id = al.album_id
    JOIN artist ar ON al.artist_id = ar.artist_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),
country_metrics AS (
    SELECT
        country,
        SUM(total_spent) AS revenue,
        COUNT(*) AS customers,
        ROUND(AVG(total_spent), 2) AS avg_customer_revenue,
        ROUND(AVG(avg_invoice_value), 2) AS avg_invoice,
        SUM(unique_genres) AS genres,
        AVG(unique_artists) AS customer_diversity
    FROM customer_profile
    GROUP BY country
),
country_rankings AS (
    SELECT *,
        (revenue*0.40 + customers*0.20 + avg_customer_revenue*0.15
         + avg_invoice*0.10 + genres*0.10 + customer_diversity*0.05) AS performance_score,
        RANK() OVER (
            ORDER BY (revenue*0.40 + customers*0.20 + avg_customer_revenue*0.15
                      + avg_invoice*0.10 + genres*0.10 + customer_diversity*0.05) DESC
        ) AS country_rank
    FROM country_metrics
)
SELECT * FROM country_rankings WHERE country_rank = 1;

WITH customer_profile AS (
    SELECT
        c.customer_id, c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    GROUP BY c.customer_id, c.country
),
country_metrics AS (
    SELECT
        country,
        SUM(total_spent) AS revenue
    FROM customer_profile
    GROUP BY country
)
SELECT
    country,
    revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_percentage
FROM country_metrics;


-- 5e. Top Employee by Revenue
WITH employee_revenue AS (
    SELECT
        e.employee_id, e.first_name, e.last_name,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM employee e
    JOIN customer c ON e.employee_id = c.support_rep_id
    JOIN invoice i ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    GROUP BY e.employee_id, e.first_name, e.last_name
)
SELECT * FROM employee_revenue
ORDER BY revenue DESC
LIMIT 1;


-- 5f. Top Artist by Revenue
WITH artist_revenue AS (
    SELECT
        ar.name,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM artist ar
    JOIN album al ON ar.artist_id = al.artist_id
    JOIN track t ON al.album_id = t.album_id
    JOIN invoice_line il ON t.track_id = il.track_id
    GROUP BY ar.name
)
SELECT * FROM artist_revenue
ORDER BY revenue DESC
LIMIT 1;


-- 5g. Top Album by Revenue
WITH album_revenue AS (
    SELECT
        al.title,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM album al
    JOIN track t ON al.album_id = t.album_id
    JOIN invoice_line il ON t.track_id = il.track_id
    GROUP BY al.title
)
SELECT * FROM album_revenue
ORDER BY revenue DESC
LIMIT 1;