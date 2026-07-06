# SQL Foundations for Data Science

## Project Overview

This project demonstrates the basics of SQL using PostgreSQL by importing the Superstore Sales dataset into a PostgreSQL database and performing basic SQL queries.

## Dataset

- **Name:** Superstore Sales Dataset
- **Source:** https://www.kaggle.com/datasets/vivek468/superstore-dataset-final/data

## Tools Used

- PostgreSQL 17
- pgAdmin 4

## Setup Steps

1. Install **PostgreSQL 17** along with **pgAdmin 4**.
2. Open **pgAdmin** and connect to the PostgreSQL server using the password created during installation.
3. Create a new database named `superstore_db`.
4. Download the Superstore Sales dataset from Kaggle and rename it to `superstore_sales.csv`.
5. Open the **Query Tool** and create the `superstore_sales` table using the provided `CREATE TABLE` statement.
6. Right-click the `superstore_sales` table and select **Import/Export Data**.
7. Select the `superstore_sales.csv` file.
8. Configure the import settings:
   - **Format:** CSV
   - **Header:** Enabled
   - **Delimiter:** `,`
   - **Quote:** `"`
   - **Escape:** `"`
   - **Encoding:** `UTF-8`
9. Click **OK** to import the dataset.
10. Verify the import by running:

```sql
SELECT COUNT(*) FROM superstore_sales;
```

## Verification Queries

Display the first 10 rows:

```sql
SELECT *
FROM superstore_sales
LIMIT 10;
```

Display the table structure:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'superstore_sales';
```

## Troubleshooting

During the setup, the following issues were encountered and resolved:

- The first import failed because the table was created without any columns. The table was recreated using a proper `CREATE TABLE` statement.
- The import then failed because PostgreSQL tried to import the first row (column names) as data. This was fixed by enabling the **Header** option.
- The CSV contained dates in `MM/DD/YYYY` format, which caused date parsing errors. The `order_date` and `ship_date` columns were temporarily created as `TEXT` to allow the import.
- An `invalid UTF-8 encoding` error appeared during troubleshooting, but the actual cause was identified later.
- The final issue was an **"unterminated CSV quoted field"** error. It was resolved by changing the **Escape** character from a single quote (`'`) to a double quote (`"`), allowing PostgreSQL to correctly read quoted values containing commas and quotation marks.

## Project Files

- `README.md`
- `concept_check.md`
- `superstore_sales.csv`
- SQL script used to create the table
- screenshots
