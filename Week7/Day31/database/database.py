"""
database.py
-----------

Creates the SQLite database used for structured retrieval.
"""

import sqlite3

import pandas as pd

from app import config


class PropertyDatabase:
    """
    Builds the SQLite database from the structured CSV files.
    """

    def __init__(self):

        self.database_path = config.SQL_DATABASE_PATH
        self.structured_dir = config.STRUCTURED_DATA_DIR

    def build_database(self):
        """
        Build the SQLite database.
        """

        conn = sqlite3.connect(self.database_path)

        csv_files = {
            "properties": "properties.csv",
            "agents": "agents.csv",
            "payment_plans": "payment_plans.csv",
            "developers": "developers.csv",
            "amenities": "amenities.csv",
            "schools": "schools.csv",
            "hospitals": "hospitals.csv",
        }

        for table_name, filename in csv_files.items():

            csv_path = self.structured_dir / filename

            df = pd.read_csv(csv_path)

            df.to_sql(
                table_name,
                conn,
                if_exists="replace",
                index=False,
            )

            print(f"Loaded {table_name}")

        conn.close()

        print("\nSQLite database created successfully.")


if __name__ == "__main__":

    PropertyDatabase().build_database()