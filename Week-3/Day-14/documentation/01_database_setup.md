# Database Setup

## Objective

Prepare the AdventureWorks PostgreSQL database for the Enterprise Analytics Hackathon.

---

## Software Used

- PostgreSQL 17.10
- pgAdmin 4
- Windows 11
- AdventureWorks PostgreSQL Dataset

---

## Step 1 — Database Creation

A new PostgreSQL database named **AdventureWorks** was created using pgAdmin.

---

## Step 2 — PostgreSQL Verification

Verified the PostgreSQL installation from Command Prompt.

```bash
psql --version
```

Output:

```text
psql (PostgreSQL) 17.10
```

---

## Step 3 — Running the Installation Script

Navigated to PostgreSQL's `bin` directory.

```bash
cd "C:\Program Files\PostgreSQL\17\bin"
```

Executed the installation script.

```bash
psql -U postgres -d AdventureWorks -f install.sql
```

---

## Step 4 — Database Objects Created

The installation successfully created numerous database objects, including:

- Schemas
- Tables
- Views
- Functions
- Domains
- Extensions
- Constraints
- Indexes

The primary schemas include:

- Person
- HumanResources
- Production
- Purchasing
- Sales

---

## Step 5 — Installation Results

During execution, PostgreSQL imported a large amount of sample data using `COPY` statements.

Example:

```
COPY 113443
COPY 89253
COPY 31465
```

---

## Step 6 — Installation Messages

Several data import warnings and foreign key constraint messages appeared while executing the installation script.

Examples included:

- Invalid input syntax
- Foreign key constraint violations
- Missing reference records

Despite these messages, the installation completed successfully and the required database objects were created.

The internship team confirmed that these messages are expected for the provided AdventureWorks dataset and do not affect the exercises.

---

## Step 7 — Verification

After installation:

- Database schemas were visible in pgAdmin.
- Tables were successfully created.
- Views were generated.
- The database was ready for exploration and SQL analytics.

---

## Status

✅ PostgreSQL configured

✅ AdventureWorks installed

✅ Database verified

✅ Ready for analytical SQL development
