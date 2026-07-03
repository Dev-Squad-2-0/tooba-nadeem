# AFL Match Context Integration

## Overview

This project enriches the AFL Round-by-Round Player Performance dataset by integrating it with the Team Match dataset to provide additional match context, including home/away status, venue, and crowd attendance. The enriched dataset enables more comprehensive analysis of player performance under different match conditions.

## Objectives

- Identify the appropriate merge keys between the two datasets.
- Integrate match context into the player performance dataset.
- Validate the accuracy of the merge.
- Analyze player performance using the enriched dataset.
- Report data quality issues and assumptions.

## Files

- `Day5_AFL_Match_Context_Integration.ipynb` – Complete analysis notebook.
- `enriched_round_by_round_stats.csv` – Final enriched dataset.
- `home_vs_away.png` – Home vs Away performance visualization.
- `crowd_vs_fantasy.png` – Crowd Attendance vs Fantasy Points visualization.
- `venue_performance.png` – Top 10 Venues by Average Fantasy Points visualization.

## Project Workflow

1. Loaded the Round-by-Round and Team Match datasets.
2. Identified a composite merge key using:
   - `year`
   - `round`
   - `team`
   - `match_date`
3. Cleaned team names by:
   - Removing leading/trailing whitespace.
   - Standardizing abbreviated team names (e.g., `W. Bulldogs` → `Western Bulldogs`).
4. Merged the datasets to enrich player records with:
   - Home/Away status
   - Venue
   - Crowd attendance
5. Validated the merge by checking:
   - Unmatched records
   - Duplicate records
   - Row count consistency
   - Missing values
6. Performed contextual analysis on:
   - Home vs Away performance
   - Crowd attendance vs Fantasy Points
   - Venue-wise average player performance
7. Exported the final enriched dataset.

## Key Findings

- All player records were successfully matched after cleaning inconsistent team names.
- No duplicate player records were introduced during the merge.
- The total number of player records remained unchanged.
- Players scored slightly higher fantasy points in home matches than away matches.
- Crowd attendance showed almost no correlation with fantasy points.
- Player performance varied across different venues.

## Technologies Used

- Python
- Pandas
- Matplotlib
- Jupyter Notebook
