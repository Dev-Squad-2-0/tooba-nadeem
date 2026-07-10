-- Database Exploration

-- Explore schemas
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
ORDER BY table_schema, table_name;

-- Explore domains
-- Domain 1 — Sales
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'sales'
ORDER BY table_name;

-- exploring individual tables
SELECT *
FROM sales.customer
LIMIT 5;

SELECT *
FROM sales.salesorderheader
LIMIT 5;

SELECT *
FROM sales.salesorderdetail
LIMIT 5;

-- Domain 2 — Production
SELECT table_name
FROM information_schema.tables
WHERE table_schema='production'
ORDER BY table_name;

-- inspecting individual tables
SELECT *
FROM production.product
LIMIT 5;

SELECT *
FROM production.productsubcategory
LIMIT 5;

SELECT *
FROM production.productcategory
LIMIT 5;

SELECT *
FROM production.productinventory
LIMIT 5;

-- Domain 3 — Person
SELECT table_name
FROM information_schema.tables
WHERE table_schema='person'
ORDER BY table_name;

SELECT *
FROM person.person
LIMIT 5;

-- Domain 4 — Human Resources
SELECT table_name
FROM information_schema.tables
WHERE table_schema='humanresources'
ORDER BY table_name;

SELECT *
FROM humanresources.employee
LIMIT 5;


-- Domain 5 — Purchasing
SELECT table_name
FROM information_schema.tables
WHERE table_schema='purchasing'
ORDER BY table_name;

SELECT *
FROM purchasing.vendor
LIMIT 5;

SELECT *
FROM purchasing.purchaseorderheader
LIMIT 5;

SELECT *
FROM purchasing.purchaseorderdetail
LIMIT 5;

SELECT *
FROM purchasing.productvendor
LIMIT 5;

SELECT *
FROM purchasing.shipmethod
LIMIT 5;


-- Domain 6 — Sales Territory
SELECT *
FROM sales.salesterritory
LIMIT 5;

SELECT *
FROM sales.salesterritoryhistory
LIMIT 5;
