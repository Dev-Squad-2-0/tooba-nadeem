------------------------------------------------------------
-- TASK 4: Country Expansion Strategy
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
    SELECT
        *,
        (revenue*0.40 + customers*0.20 + avg_customer_revenue*0.15
         + avg_invoice*0.10 + genres*0.10 + customer_diversity*0.05) AS performance_score,
        RANK() OVER (
            ORDER BY (revenue*0.40 + customers*0.20 + avg_customer_revenue*0.15
                      + avg_invoice*0.10 + genres*0.10 + customer_diversity*0.05) DESC
        ) AS country_rank
    FROM country_metrics
)
SELECT * FROM country_rankings
WHERE country_rank <= 3;