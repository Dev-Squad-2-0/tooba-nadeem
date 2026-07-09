/*
===========================================================
Bonus Challenge
Refactor your solution into a single SQL script where every step builds upon the previous one using chained CTEs.
A strong solution might follow a structure similar to:
•	Customer Profile
•	Customer Segments
•	Favorite Genres
•	Country Metrics
•	Country Ranking
•	Artist Revenue
•	Final Executive Dashboard
The final script should read like a complete data pipeline rather than isolated queries.
============================================================
*/

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
),

employee_revenue AS (
    SELECT
        e.employee_id,
        e.first_name,
        e.last_name,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM employee e
    JOIN customer c      ON e.employee_id = c.support_rep_id
    JOIN invoice i       ON c.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    GROUP BY e.employee_id, e.first_name, e.last_name
),

top_employee AS (
    SELECT employee_id, first_name, last_name, revenue
    FROM (
        SELECT *, RANK() OVER (ORDER BY revenue DESC) AS rnk
        FROM employee_revenue
    ) x
    WHERE rnk = 1
),

artist_revenue AS (
    SELECT
        ar.name AS artist_name,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM artist ar
    JOIN album al        ON ar.artist_id = al.artist_id
    JOIN track t         ON al.album_id = t.album_id
    JOIN invoice_line il ON t.track_id = il.track_id
    GROUP BY ar.name
),

top_artist AS (
    SELECT artist_name, revenue
    FROM (
        SELECT *, RANK() OVER (ORDER BY revenue DESC) AS rnk
        FROM artist_revenue
    ) x
    WHERE rnk = 1
),

album_revenue AS (
    SELECT
        al.title AS album_title,
        SUM(il.unit_price * il.quantity) AS revenue
    FROM album al
    JOIN track t         ON al.album_id = t.album_id
    JOIN invoice_line il ON t.track_id = il.track_id
    GROUP BY al.title
),

top_album AS (
    SELECT album_title, revenue
    FROM (
        SELECT *, RANK() OVER (ORDER BY revenue DESC) AS rnk
        FROM album_revenue
    ) x
    WHERE rnk = 1
),

top_customer_per_segment AS (
    SELECT customer_segment, first_name, last_name, total_spent
    FROM (
        SELECT
            customer_segment, first_name, last_name, total_spent,
            ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY total_spent DESC) AS rn
        FROM customer_segments
    ) x
    WHERE rn = 1
),

top_genre_per_segment AS (
    SELECT customer_segment, genre, customers
    FROM (
        SELECT
            customer_segment, genre, COUNT(*) AS customers,
            ROW_NUMBER() OVER (PARTITION BY customer_segment ORDER BY COUNT(*) DESC) AS rn
        FROM marketing_recommendation
        GROUP BY customer_segment, genre
    ) x
    WHERE rn = 1
)

/*
------------------------------------------------------------
FINAL EXECUTIVE DASHBOARD
(all CTEs unioned into one report;
sort_order controls the section order just to display data in order,
all cast to text so columns can merged using 'UNION ALL')
------------------------------------------------------------
*/

SELECT 1 AS sort_order, 'Customer Segment Summary' AS report_section,
       customer_segment AS dimension_1, NULL AS dimension_2,
       COUNT(*)::text AS metric_1, NULL AS metric_2
FROM customer_segments
GROUP BY customer_segment

UNION ALL

SELECT 2, 'Revenue by Segment',
       customer_segment, NULL,
       SUM(total_spent)::text, NULL
FROM customer_segments
GROUP BY customer_segment

UNION ALL

SELECT 3, 'Top Customer per Segment',
       customer_segment, first_name || ' ' || last_name,
       total_spent::text, NULL
FROM top_customer_per_segment

UNION ALL

SELECT 4, 'Top Genre per Segment',
       customer_segment, genre,
       customers::text, NULL
FROM top_genre_per_segment

UNION ALL

SELECT 5, 'Best Performing Country',
       country, NULL,
       revenue::text, ROUND(performance_score,2)::text
FROM country_rankings
WHERE country_rank = 1

UNION ALL

SELECT 6, 'Revenue Contribution by Country',
       country, NULL,
       revenue::text,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)::text || '%'
FROM country_metrics

UNION ALL

SELECT 7, 'Top Employee by Revenue',
       first_name || ' ' || last_name, NULL,
       revenue::text, NULL
FROM top_employee

UNION ALL

SELECT 8, 'Top Artist by Revenue',
       artist_name, NULL,
       revenue::text, NULL
FROM top_artist

UNION ALL

SELECT 9, 'Top Album by Revenue',
       album_title, NULL,
       revenue::text, NULL
FROM top_album

ORDER BY sort_order;
