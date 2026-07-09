------------------------------------------------------------
-- TASK 3: Personalized Marketing Recommendation
------------------------------------------------------------

WITH customer_profile AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.country,
        SUM(il.unit_price * il.quantity) AS total_spent,
        COUNT(DISTINCT i.invoice_id) AS total_invoices,
        SUM(il.quantity) AS total_tracks,
        COUNT(DISTINCT g.genre_id) AS unique_genres,
        COUNT(DISTINCT ar.artist_id) AS unique_artists,
        COUNT(DISTINCT DATE_TRUNC('month', i.invoice_date)) AS purchase_months,
        ROUND(SUM(il.unit_price * il.quantity) / COUNT(DISTINCT i.invoice_id), 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice i      ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t        ON il.track_id = t.track_id
    JOIN genre g        ON t.genre_id = g.genre_id
    JOIN album al       ON t.album_id = al.album_id
    JOIN artist ar      ON al.artist_id = ar.artist_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.country
),
customer_segments AS (
    SELECT
        *,
        CASE
            WHEN total_spent >= 40 AND total_invoices >= 7 AND unique_genres >= 5 THEN 'Platinum'
            WHEN total_spent >= 25 AND total_invoices >= 5 THEN 'Gold'
            WHEN total_spent >= 10 AND total_invoices >= 2 THEN 'Silver'
            ELSE 'Bronze'
        END AS customer_segment
    FROM customer_profile
),
genre_counts AS (
    SELECT
        c.customer_id,
        g.name AS genre,
        COUNT(*) AS purchases
    FROM customer c
    JOIN invoice i      ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t        ON il.track_id = t.track_id
    JOIN genre g        ON t.genre_id = g.genre_id
    GROUP BY c.customer_id, g.name
),
favorite_genres AS (
    SELECT customer_id, genre, purchases
    FROM (
        SELECT
            customer_id, genre, purchases,
            ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY purchases DESC) AS rn
        FROM genre_counts
    ) x
    WHERE rn = 1
),
marketing_recommendation AS (
    SELECT
        cs.*,
        fg.genre,
        CASE
            WHEN cs.customer_segment = 'Platinum' THEN 'Early access to new releases'
            WHEN cs.customer_segment = 'Gold'     THEN 'Album bundle discounts'
            WHEN cs.customer_segment = 'Silver'   THEN 'Genre-based promotions'
            ELSE 'First purchase coupon'
        END AS campaign
    FROM customer_segments cs
    LEFT JOIN favorite_genres fg ON cs.customer_id = fg.customer_id
)
SELECT * FROM marketing_recommendation;