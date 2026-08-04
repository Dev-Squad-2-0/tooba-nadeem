"""
sql_retriever.py
----------------

Structured retrieval using SQLite.
"""

import sqlite3

from app import config


class SQLRetriever:

    def __init__(self):

        self.conn = sqlite3.connect(config.SQL_DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row

    def _query(
    self,
    sql: str,
    params: tuple = (),
    ):

        cursor = self.conn.execute(sql, params)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    # --------------------------------------------------
    # Prices
    # --------------------------------------------------

    def get_prices(self):

        return self._query("""
            SELECT
                project_name,
                city,
                price_range_min_pkr,
                price_range_max_pkr
            FROM properties
        """)

    # --------------------------------------------------
    # Availability
    # --------------------------------------------------

    def get_availability(self):

        return self._query("""
            SELECT
                project_name,
                status,
                total_units
            FROM properties
        """)

    # --------------------------------------------------
    # Plot / Unit Sizes
    # --------------------------------------------------

    def get_plot_sizes(self):

        return self._query("""
            SELECT
                project_name,
                size_range_sqft
            FROM properties
        """)

    # --------------------------------------------------
    # Agents
    # --------------------------------------------------

    def get_agents(self):

        return self._query("""
            SELECT
                name,
                city,
                specialization,
                phone,
                email
            FROM agents
        """)

    # --------------------------------------------------
    # Amenities
    # --------------------------------------------------

    def get_amenities(self):
        """
        Return all property amenities.
        """

        return self._query("""
            SELECT
                property_id,
                amenity_name
            FROM amenities
        """)


    # --------------------------------------------------
    # Property Price
    # --------------------------------------------------

    def get_property_price(
        self,
        project_name: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                city,
                price_range_min_pkr,
                price_range_max_pkr
            FROM properties
            WHERE LOWER(project_name)=LOWER(?)
            """,
            (project_name,),
        )


    # --------------------------------------------------
    # Property Availability
    # --------------------------------------------------

    def get_property_availability(
        self,
        project_name: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                status,
                total_units
            FROM properties
            WHERE LOWER(project_name)=LOWER(?)
            """,
            (project_name,),
        )


    # --------------------------------------------------
    # Plot Size
    # --------------------------------------------------

    def get_plot_size(
        self,
        project_name: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                size_range_sqft
            FROM properties
            WHERE LOWER(project_name)=LOWER(?)
            """,
            (project_name,),
        )


    # --------------------------------------------------
    # Agent for Property
    # --------------------------------------------------

    def get_property_agent(
        self,
        property_id: str,
    ):

        return self._query(
            """
            SELECT
                name,
                city,
                phone,
                email,
                specialization
            FROM agents
            WHERE assigned_property_ids = ?
            """,
            (property_id,),
        )


    # --------------------------------------------------
    # Filter by City
    # --------------------------------------------------

    def get_properties_by_city(
        self,
        city: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                property_type,
                status,
                price_range_min_pkr,
                price_range_max_pkr
            FROM properties
            WHERE LOWER(city)=LOWER(?)
            """,
            (city,),
        )


    # --------------------------------------------------
    # Filter by Budget
    # --------------------------------------------------

    def get_properties_by_budget(
        self,
        budget: int,
    ):

        return self._query(
            """
            SELECT
                project_name,
                city,
                property_type,
                price_range_min_pkr,
                price_range_max_pkr
            FROM properties
            WHERE price_range_min_pkr <= ?
            ORDER BY price_range_min_pkr
            """,
            (budget,),
        )


    # --------------------------------------------------
    # Filter by Property Type
    # --------------------------------------------------

    def get_properties_by_type(
        self,
        property_type: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                city,
                property_type,
                price_range_min_pkr,
                price_range_max_pkr
            FROM properties
            WHERE LOWER(property_type)=LOWER(?)
            """,
            (property_type,),
        )


    # --------------------------------------------------
    # Find Property by Developer
    # --------------------------------------------------

    def get_properties_by_developer(
        self,
        developer_id: str,
    ):

        return self._query(
            """
            SELECT
                project_name,
                city,
                property_type,
                status
            FROM properties
            WHERE developer_id = ?
            """,
            (developer_id,),
        )

    def close(self):

        self.conn.close()


    