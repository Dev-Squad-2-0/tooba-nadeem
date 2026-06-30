# AFL Data Cleaning and Validation

## Overview

This project focuses on cleaning, validating, and merging two AFL datasets to create a single analysis-ready dataset.

The tasks performed include data quality assessment, handling missing and invalid values, removing duplicate records, standardizing data formats, validating the cleaned data, and merging the datasets.

## Files

- `afl_players_info_raw.csv` – Original player information dataset
- `afl_players_seasonal_stats_raw.csv` – Original seasonal statistics dataset
- `cleaned_players_info.csv` – Cleaned player information dataset
- `cleaned_seasonal_stats.csv` – Cleaned seasonal statistics dataset
- `merged_players.csv` – Final merged analysis-ready dataset
- `AFL_Data_Cleaning.ipynb` – Jupyter Notebook containing all cleaning, validation, and merging steps

## Data Cleaning Performed

- Removed duplicate records
- Standardized `player_id` data type for consistent merging
- Converted date columns to datetime format
- Replaced invalid player weights (`0 kg`) with the median weight
- Treated negative `games_played` values as missing (`NaN`)
- Standardized team names by removing extra spaces and using consistent capitalization
- Validated missing values and retained those representing unavailable statistics

## Validation

The project includes:

- Row counts before and after cleaning
- Missing values summary
- Duplicate records removed
- Merge validation
- Identification of unmatched `player_id` values

## Output

The final output is a cleaned and merged dataset that is ready for further data analysis and visualization.

## Tools Used

- Python
- Pandas
- Jupyter Notebook
