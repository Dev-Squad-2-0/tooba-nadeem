/*
=========================================================
Enterprise Analytics Hackathon
Analytics Layer
AdventureWorks PostgreSQL

Task 1
Reusable Analytics Layer
=========================================================
*/

---------------------------------------------------------
-- Create Analytics Schema
---------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS analytics;

--Layer 1 — Base Views
-- 1. customer_base
---------------------------------------------------------
-- customer_base
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.customer_base AS

SELECT
    c.customerid,
    c.personid,
    p.firstname,
    p.lastname,
    p.persontype,
    p.emailpromotion,
    a.city,
    sp.name AS state,
    cr.name AS country
FROM sales.customer c
LEFT JOIN person.person p
       ON c.personid = p.businessentityid
LEFT JOIN person.businessentityaddress bea
       ON p.businessentityid = bea.businessentityid
LEFT JOIN person.address a
       ON bea.addressid = a.addressid
LEFT JOIN person.stateprovince sp
       ON a.stateprovinceid = sp.stateprovinceid
LEFT JOIN person.countryregion cr
       ON sp.countryregioncode = cr.countryregioncode;

--2. product_base   
---------------------------------------------------------
-- product_base
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.product_base AS

SELECT
    p.productid,
    p.name AS product_name,
    p.productnumber,
    p.color,
    p.standardcost,
    p.listprice,
    p.size,
    pc.name AS category,
    ps.name AS subcategory
FROM production.product p
LEFT JOIN production.productsubcategory ps
       ON p.productsubcategoryid = ps.productsubcategoryid
LEFT JOIN production.productcategory pc
       ON ps.productcategoryid = pc.productcategoryid;

-- 3. employee_base
---------------------------------------------------------
-- employee_base
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.employee_base AS

SELECT
    e.businessentityid,
    p.firstname,
    p.lastname,
    e.jobtitle,
    e.hiredate,
    d.name AS department,
    s.name AS shift
FROM humanresources.employee e
LEFT JOIN person.person p
       ON e.businessentityid = p.businessentityid
LEFT JOIN humanresources.employeedepartmenthistory edh
       ON e.businessentityid = edh.businessentityid
      AND edh.enddate IS NULL
LEFT JOIN humanresources.department d
       ON edh.departmentid = d.departmentid
LEFT JOIN humanresources.shift s
       ON edh.shiftid = s.shiftid;

-- -- 4. order_base
---------------------------------------------------------
-- order_base
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.order_base AS

SELECT
    soh.salesorderid,
    soh.orderdate,
    soh.customerid,
    soh.salespersonid,
    soh.territoryid,

    sod.productid,
    sod.orderqty,
    sod.unitprice,
    sod.unitpricediscount,

    -- Calculate line total manually
    (sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount)) AS line_total

FROM sales.salesorderheader soh
JOIN sales.salesorderdetail sod
ON soh.salesorderid = sod.salesorderid;

-- -- 5. territory_base
-- ---------------------------------------------------------
-- -- territory_base
-- ---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.territory_base AS

SELECT
    territoryid,
    name AS territory,
    countryregioncode,
    "group"
FROM sales.salesterritory;

-- 6. inventory_base
---------------------------------------------------------
-- inventory_base
---------------------------------------------------------
CREATE OR REPLACE VIEW analytics.inventory_base AS

SELECT
    pi.productid,
    p.name AS product_name,
    pi.locationid,
    pi.quantity
FROM production.productinventory pi
LEFT JOIN production.product p
       ON pi.productid = p.productid;

-- 7. purchase_base
---------------------------------------------------------
-- purchase_base
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.purchase_base AS

SELECT

    poh.purchaseorderid,

    poh.orderdate,

    pod.productid,

    pod.orderqty,

    pod.unitprice,

    (pod.orderqty * pod.unitprice) AS purchase_cost

FROM purchasing.purchaseorderheader poh

JOIN purchasing.purchaseorderdetail pod

ON poh.purchaseorderid = pod.purchaseorderid;

-- 8. vendor_base
---------------------------------------------------------
-- vendor_base
---------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vendor_base AS

SELECT

    pv.businessentityid AS vendor_id,

    v.name AS vendor_name,

    pv.productid,

    pv.standardprice,

    pv.averageleadtime

FROM purchasing.productvendor pv

LEFT JOIN purchasing.vendor v

ON pv.businessentityid = v.businessentityid;


-- Layer 2 — Materialized Views
-- 1. customer_metrics
---------------------------------------------------------
-- customer_metrics
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.customer_metrics;
CREATE MATERIALIZED VIEW analytics.customer_metrics AS

SELECT
    cb.customerid,
    CONCAT(cb.firstname, ' ', cb.lastname) AS customer_name,
    cb.city,
    cb.state,
    cb.country,

    COUNT(DISTINCT ob.salesorderid) AS total_orders,

    SUM(ob.line_total) AS total_sales,

    ROUND(AVG(ob.line_total), 2) AS average_order_value,

    MAX(ob.orderdate) AS last_order_date

FROM analytics.customer_base cb

LEFT JOIN analytics.order_base ob
       ON cb.customerid = ob.customerid

GROUP BY
    cb.customerid,
    cb.firstname,
    cb.lastname,
    cb.city,
    cb.state,
    cb.country;

-- 2. product_metrics
---------------------------------------------------------
-- product_metrics
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.product_metrics;
CREATE MATERIALIZED VIEW analytics.product_metrics AS

SELECT
    pb.productid,
    pb.product_name,
    pb.category,
    pb.subcategory,

    SUM(ob.orderqty) AS total_units_sold,

    SUM(ob.line_total) AS total_revenue,

    ROUND(AVG(ob.unitprice),2) AS average_selling_price,

    COUNT(DISTINCT ob.salesorderid) AS orders_count

FROM analytics.product_base pb

LEFT JOIN analytics.order_base ob
       ON pb.productid = ob.productid

GROUP BY
    pb.productid,
    pb.product_name,
    pb.category,
    pb.subcategory;
	
-- 3. employee_metrics
---------------------------------------------------------
-- employee_metrics
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.employee_metrics;
CREATE MATERIALIZED VIEW analytics.employee_metrics AS

SELECT
    eb.businessentityid,
    CONCAT(eb.firstname,' ',eb.lastname) AS employee_name,
    eb.jobtitle,
    eb.department,
    eb.shift,

    COUNT(DISTINCT ob.salesorderid) AS total_orders_handled,

    SUM(ob.line_total) AS sales_generated

FROM analytics.employee_base eb

LEFT JOIN analytics.order_base ob
       ON eb.businessentityid = ob.salespersonid

GROUP BY
    eb.businessentityid,
    eb.firstname,
    eb.lastname,
    eb.jobtitle,
    eb.department,
    eb.shift;

-- 4. territory_metrics
---------------------------------------------------------
-- territory_metrics
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.territory_metrics;
CREATE MATERIALIZED VIEW analytics.territory_metrics AS

SELECT
    tb.territoryid,
    tb.territory,
    tb.countryregioncode,
    tb."group",

    COUNT(DISTINCT ob.salesorderid) AS total_orders,

    COUNT(DISTINCT ob.customerid) AS total_customers,

    SUM(ob.line_total) AS territory_sales

FROM analytics.territory_base tb

LEFT JOIN analytics.order_base ob
       ON tb.territoryid = ob.territoryid

GROUP BY
    tb.territoryid,
    tb.territory,
    tb.countryregioncode,
    tb."group";

-- 5. monthly_revenue
---------------------------------------------------------
-- monthly_revenue
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.monthly_revenue;
CREATE MATERIALIZED VIEW analytics.monthly_revenue AS

SELECT

    DATE_TRUNC('month', orderdate) AS sales_month,

    COUNT(DISTINCT salesorderid) AS total_orders,

    SUM(line_total) AS revenue

FROM analytics.order_base

GROUP BY DATE_TRUNC('month', orderdate)

ORDER BY sales_month;

-- 6. inventory_metrics
---------------------------------------------------------
-- inventory_metrics
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.inventory_metrics;
CREATE MATERIALIZED VIEW analytics.inventory_metrics AS

SELECT

    productid,

    product_name,

    locationid,

    quantity,

    CASE
        WHEN quantity < 10
        THEN 'Low Stock'
        ELSE 'Sufficient'
    END AS inventory_status

FROM analytics.inventory_base;

-- Refresh Commands
REFRESH MATERIALIZED VIEW analytics.customer_metrics;
REFRESH MATERIALIZED VIEW analytics.product_metrics;
REFRESH MATERIALIZED VIEW analytics.employee_metrics;
REFRESH MATERIALIZED VIEW analytics.territory_metrics;
REFRESH MATERIALIZED VIEW analytics.monthly_revenue;
REFRESH MATERIALIZED VIEW analytics.inventory_metrics;

-- Low Stock Products
---------------------------------------------------------
-- low_stock_products
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.low_stock_products AS

SELECT *

FROM analytics.inventory_metrics

WHERE inventory_status = 'Low Stock';

-- Layer 3 — Analytical Views
-- 1. customer_segments
---------------------------------------------------------
-- customer_segments
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.customer_segments AS

SELECT
    customerid,
    customer_name,
    city,
    state,
    country,
    total_orders,
    total_sales,
    average_order_value,

    CASE
        WHEN total_sales >= 100000 THEN 'Platinum'
        WHEN total_sales >= 50000 THEN 'Gold'
        WHEN total_sales >= 10000 THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_segment

FROM analytics.customer_metrics;

-- 2. product_rankings
---------------------------------------------------------
-- product_rankings
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.product_rankings AS

SELECT
    *,
    RANK() OVER(
        ORDER BY total_revenue DESC
    ) AS revenue_rank

FROM analytics.product_metrics;

-- 3. employee_rankings
---------------------------------------------------------
-- employee_rankings
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.employee_rankings AS

SELECT
    *,
    RANK() OVER(
        ORDER BY sales_generated DESC
    ) AS sales_rank

FROM analytics.employee_metrics;

--4. territory_rankings
---------------------------------------------------------
-- territory_rankings
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.territory_rankings AS

SELECT
    *,
    RANK() OVER(
        ORDER BY territory_sales DESC
    ) AS territory_rank

FROM analytics.territory_metrics;

-- 5. vendor_rankings
---------------------------------------------------------
-- vendor_rankings
---------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vendor_rankings AS

SELECT

    vendor_name,

    COUNT(productid) AS supplied_products,

    AVG(averageleadtime) AS avg_lead_time,

    AVG(standardprice) AS avg_vendor_price,

    RANK() OVER(
        ORDER BY COUNT(productid) DESC
    ) AS vendor_rank

FROM analytics.vendor_base

GROUP BY vendor_name;


-- Layer 4 — Executive KPI Summary
---------------------------------------------------------
-- exec_kpi_summary
---------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS analytics.exec_kpi_summary;
CREATE MATERIALIZED VIEW analytics.exec_kpi_summary AS

SELECT

    (SELECT SUM(total_sales)
     FROM analytics.customer_metrics) AS total_revenue,

    (SELECT SUM(total_orders)
     FROM analytics.customer_metrics) AS total_orders,

    (SELECT COUNT(*)
     FROM analytics.customer_metrics) AS total_customers,

    (SELECT COUNT(*)
     FROM analytics.product_metrics) AS total_products,

    (SELECT AVG(total_sales)
     FROM analytics.customer_metrics) AS avg_customer_sales,

    (SELECT MAX(revenue)
     FROM analytics.monthly_revenue) AS best_month_revenue;

 -- Refresh it
 REFRESH MATERIALIZED VIEW analytics.exec_kpi_summary;


 /*
=========================================================
Task 2
Business SQL Pipeline
=========================================================
*/
--Stage 1 — Quarterly Revenue
---------------------------------------------------------
-- quarterly_revenue
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.quarterly_revenue AS

SELECT

    DATE_TRUNC('quarter', sales_month) AS sales_quarter,

    SUM(revenue) AS quarterly_revenue,

    SUM(total_orders) AS total_orders

FROM analytics.monthly_revenue

GROUP BY DATE_TRUNC('quarter', sales_month)

ORDER BY sales_quarter;

-- Stage 2 — Monthly Sales Growth
---------------------------------------------------------
-- sales_growth
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.sales_growth AS

SELECT

    sales_month,

    revenue,

    LAG(revenue) OVER(
        ORDER BY sales_month
    ) AS previous_month,

    ROUND(

        (
            revenue -
            LAG(revenue) OVER(
                ORDER BY sales_month
            )
        )

        /

        NULLIF(
            LAG(revenue) OVER(
                ORDER BY sales_month
            ),
            0
        )

        *100,

        2

    ) AS growth_percent

FROM analytics.monthly_revenue;

-- Stage 3 — Best Selling Products
---------------------------------------------------------
-- best_selling_products
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.best_selling_products AS

SELECT *

FROM analytics.product_rankings

WHERE revenue_rank <= 10;

-- Stage 4 — Lowest Performing Products
---------------------------------------------------------
-- lowest_performing_products
---------------------------------------------------------
CREATE OR REPLACE VIEW analytics.lowest_performing_products AS

SELECT *

FROM
(
    SELECT
        *,
        RANK() OVER(
            ORDER BY total_revenue ASC
        ) AS lowest_rank

    FROM analytics.product_metrics
) p

WHERE lowest_rank <= 10;

-- Stage 5 — Customer Lifetime Value
---------------------------------------------------------
-- customer_lifetime_value
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.customer_lifetime_value AS

SELECT

    customerid,

    customer_name,

    total_sales AS lifetime_value,

    total_orders,

    average_order_value

FROM analytics.customer_metrics;

-- Customer Order Behavior (Added to demonstrate Conditional Aggregation)
---------------------------------------------------------
-- customer_order_behavior
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.customer_order_behavior AS

SELECT

    customerid,

    COUNT(*) AS total_orders,

    SUM(
        CASE
            WHEN line_total >= 1000
            THEN line_total
            ELSE 0
        END
    ) AS high_value_sales,


    SUM(
        CASE
            WHEN line_total < 1000
            THEN line_total
            ELSE 0
        END
    ) AS normal_sales


FROM analytics.order_base

GROUP BY customerid;

-- Stage 6 — Repeat Customers
---------------------------------------------------------
-- repeat_customers
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.repeat_customers AS

SELECT *

FROM analytics.customer_metrics

WHERE total_orders > 1;

-- Stage 7 — Customer Retention
---------------------------------------------------------
-- customer_retention
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.customer_retention AS

SELECT

    COUNT(*) AS repeat_customers,

    ROUND(

        COUNT(*) * 100.0

        /

        (
            SELECT COUNT(*)
            FROM analytics.customer_metrics
        ),

        2

    ) AS retention_rate

FROM analytics.customer_metrics

WHERE total_orders > 1;


-- Stage 8 — Product Profitability
---------------------------------------------------------
-- product_profitability
---------------------------------------------------------
CREATE OR REPLACE VIEW analytics.product_profitability AS

SELECT

    pb.productid,

    pb.product_name,

    pb.category,

    pb.subcategory,

    pm.total_units_sold,

    pm.total_revenue,

    pb.standardcost,

    ROUND(
        pm.total_revenue -
        (pb.standardcost * pm.total_units_sold),
        2
    ) AS estimated_profit

FROM analytics.product_base pb

JOIN analytics.product_metrics pm
ON pb.productid = pm.productid;


-- Stage 9 — Category Performance
---------------------------------------------------------
-- category_performance
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.category_performance AS

SELECT

    category,

    SUM(total_revenue) AS revenue,

    SUM(total_units_sold) AS units_sold

FROM analytics.product_metrics

GROUP BY category;

-- Stage 10 — Revenue Contribution
---------------------------------------------------------
-- revenue_contribution
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.revenue_contribution AS

SELECT

    employee_name,

    sales_generated,

    ROUND(

        sales_generated

        *100

        /

        (
            SELECT SUM(sales_generated)
            FROM analytics.employee_metrics
        ),

        2

    ) AS contribution_percent

FROM analytics.employee_metrics;


/*
=========================================================
Additional Executive KPI Views
=========================================================
*/
-- 1. Territory Growth
---------------------------------------------------------
-- territory_growth
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.territory_growth AS

WITH territory_monthly AS (

    SELECT

        territoryid,

        DATE_TRUNC('month', orderdate) AS sales_month,

        SUM(line_total) AS revenue

    FROM analytics.order_base

    GROUP BY
        territoryid,
        DATE_TRUNC('month', orderdate)

)

SELECT

    territoryid,

    sales_month,

    revenue,

    LAG(revenue) OVER(
        PARTITION BY territoryid
        ORDER BY sales_month
    ) AS previous_month,

    ROUND(

        (
            revenue -
            LAG(revenue) OVER(
                PARTITION BY territoryid
                ORDER BY sales_month
            )
        )

        /

        NULLIF(
            LAG(revenue) OVER(
                PARTITION BY territoryid
                ORDER BY sales_month
            ),
            0
        ) * 100,

        2

    ) AS growth_percent

FROM territory_monthly;


-- 2. Top Territories
---------------------------------------------------------
-- top_territories
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.top_territories AS

SELECT *

FROM analytics.territory_rankings

WHERE territory_rank <= 5;

-- 3. Lowest Performing Territories
---------------------------------------------------------
-- lowest_performing_territories
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.lowest_performing_territories AS

SELECT *

FROM analytics.territory_metrics

ORDER BY territory_sales

LIMIT 5;



-- 4. Supplier Performance
---------------------------------------------------------
-- supplier_performance
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.supplier_performance AS

SELECT

    vendor_name,

    supplied_products,

    avg_lead_time,

    avg_vendor_price,

    vendor_rank

FROM analytics.vendor_rankings;


-- 5. Purchasing Trends
---------------------------------------------------------
-- purchasing_trends
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.purchasing_trends AS

SELECT

    DATE_TRUNC('month', orderdate) AS purchase_month,

    COUNT(DISTINCT purchaseorderid) AS purchase_orders,

    SUM(orderqty) AS items_ordered,

    SUM(purchase_cost) AS purchasing_cost

FROM analytics.purchase_base

GROUP BY DATE_TRUNC('month', orderdate)

ORDER BY purchase_month;


-- 6. Employee Performance Comparison
---------------------------------------------------------
-- employee_performance_comparison
---------------------------------------------------------

CREATE OR REPLACE VIEW analytics.employee_performance_comparison AS

SELECT

    employee_name,

    department,

    sales_generated,

    AVG(sales_generated)
        OVER(PARTITION BY department)
        AS department_average,

    CASE

        WHEN sales_generated >
             AVG(sales_generated)
             OVER(PARTITION BY department)

        THEN 'Above Average'

        ELSE 'Below Average'

    END AS performance

FROM analytics.employee_metrics;

/*
=========================================================
Task 4
Advanced SQL Analytical Reports
=========================================================
*/

-- Report 1 
---------------------------------------------------------
-- Executive Sales Report
---------------------------------------------------------

WITH monthly AS (

    SELECT *
    FROM analytics.monthly_revenue

),

growth AS (

    SELECT *
    FROM analytics.sales_growth

),

quarterly AS (

    SELECT *
    FROM analytics.quarterly_revenue

)

SELECT

    m.sales_month,

    m.revenue,

    q.sales_quarter,

    q.quarterly_revenue,

    g.growth_percent,

    CASE

        WHEN g.growth_percent > 10 THEN 'Excellent'

        WHEN g.growth_percent > 0 THEN 'Growing'

        WHEN g.growth_percent IS NULL THEN 'N/A'

        ELSE 'Declining'

    END AS business_status

FROM monthly m

LEFT JOIN growth g
ON m.sales_month = g.sales_month

LEFT JOIN quarterly q
ON DATE_TRUNC('quarter', m.sales_month) = q.sales_quarter

ORDER BY m.sales_month;


-- Report 2
---------------------------------------------------------
-- Customer Behavior Analysis
---------------------------------------------------------

WITH customer_data AS (

    SELECT *
    FROM analytics.customer_metrics

),

segments AS (

    SELECT *
    FROM analytics.customer_segments

),

ranked_customers AS (

    SELECT

        customerid,

        customer_name,

        total_sales,

        RANK() OVER(
            ORDER BY total_sales DESC
        ) AS spending_rank

    FROM customer_data

)

SELECT

    s.customer_name,

    s.customer_segment,

    r.total_sales,

    r.spending_rank,

    s.total_orders,

    s.average_order_value

FROM segments s

JOIN ranked_customers r

ON s.customerid = r.customerid

ORDER BY spending_rank;

-- Report 3
---------------------------------------------------------
-- Product Performance Dashboard
---------------------------------------------------------

WITH profitability AS (

    SELECT *
    FROM analytics.product_profitability

),

category_summary AS (

    SELECT

        category,

        SUM(estimated_profit) AS total_profit,

        SUM(total_units_sold) AS units_sold

    FROM profitability

    GROUP BY category

),

ranked_categories AS (

    SELECT

        *,

        DENSE_RANK() OVER(
            ORDER BY total_profit DESC
        ) AS category_rank

    FROM category_summary

)

SELECT *

FROM ranked_categories

ORDER BY category_rank;


-- Report 4
---------------------------------------------------------
-- Customer Segment Summary
---------------------------------------------------------

WITH segment_summary AS (

    SELECT

        customer_segment,

        COUNT(*) AS customers,

        SUM(total_sales) AS revenue,

        AVG(total_sales) AS avg_sales

    FROM analytics.customer_segments

    GROUP BY customer_segment

),

ranked_segments AS (

    SELECT

        *,

        RANK() OVER(
            ORDER BY revenue DESC
        ) AS segment_rank

    FROM segment_summary

)

SELECT *

FROM ranked_segments

ORDER BY segment_rank;

-- Report 5
---------------------------------------------------------
-- Territory Performance Dashboard
---------------------------------------------------------

WITH territory_sales AS (

    SELECT *

    FROM analytics.territory_metrics

),

comparison AS (

    SELECT

        territory,

        territory_sales,

        total_orders,

        total_customers,

        AVG(territory_sales)
            OVER() AS average_sales

    FROM territory_sales

)

SELECT

    *,

    CASE

        WHEN territory_sales >= average_sales
        THEN 'Above Average'

        ELSE 'Below Average'

    END AS performance

FROM comparison

ORDER BY territory_sales DESC;

-- Report 6
---------------------------------------------------------
-- Monthly Sales Growth
---------------------------------------------------------

SELECT *

FROM analytics.sales_growth;


-- Report 7
---------------------------------------------------------
-- Vendor Performance Dashboard
---------------------------------------------------------

WITH vendor_stats AS (

    SELECT *

    FROM analytics.vendor_rankings

),

summary AS (

    SELECT

        *,

        AVG(avg_lead_time)
            OVER() AS overall_avg_lead_time

    FROM vendor_stats

)

SELECT

    *,

    CASE

        WHEN avg_lead_time < overall_avg_lead_time
        THEN 'Fast Supplier'

        ELSE 'Slow Supplier'

    END AS supplier_status

FROM summary

ORDER BY vendor_rank;


-- Report 8
---------------------------------------------------------
-- Executive KPI Dashboard
---------------------------------------------------------

SELECT *

FROM analytics.exec_kpi_summary;

---------------------------------------------------------
-- Refresh all Materialized Views
---------------------------------------------------------

REFRESH MATERIALIZED VIEW analytics.customer_metrics;
REFRESH MATERIALIZED VIEW analytics.product_metrics;
REFRESH MATERIALIZED VIEW analytics.employee_metrics;
REFRESH MATERIALIZED VIEW analytics.territory_metrics;
REFRESH MATERIALIZED VIEW analytics.monthly_revenue;
REFRESH MATERIALIZED VIEW analytics.inventory_metrics;
REFRESH MATERIALIZED VIEW analytics.exec_kpi_summary;
