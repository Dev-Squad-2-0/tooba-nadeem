# AFL Data Foundations – Week 6 Day 1

## Project Overview

This project focuses on exploratory data analysis (EDA), data quality assessment, feature engineering, and prediction target definition for the AFL dataset. The goal is to prepare high-quality data for future machine learning models and an AFL domain-specific assistant.

## Submission Contents

- `Week6_Day1_AFL_Data_Foundations.ipynb` – Complete notebook containing EDA, data cleaning, feature engineering, and analysis.
- `AFL_Data_Dictionary_Target_Definitions.pdf` (or `.docx`) – One-page data dictionary and prediction target definitions.
- `README.md` – Project overview and submission guide.

## Datasets Used

- `cleaned_round_by_round_stats_v2.csv`
- `cleaned_team_matches.csv`
- `cleaned_seasonal_stats.csv`

## Tasks Completed

- Performed exploratory data analysis (EDA).
- Assessed data quality, including missing values and invalid entries.
- Checked for duplicate records and data consistency.
- Engineered historical features using rolling statistics.
- Defined prediction targets for match and player performance.
- Prevented data leakage by generating features using only historical information.

## Data Quality Notes

- Negative values in statistics such as **kicks**, **handballs**, and **disposals** were treated as invalid because these statistics cannot logically be negative.
- Negative **fantasy points** were retained since fantasy scoring systems may legitimately assign negative scores.

## Author

**Name:** Tooba Nadeem  
**Internship:** NetixSol AI/ML Internship  
**Week:** 6 – Day 1
