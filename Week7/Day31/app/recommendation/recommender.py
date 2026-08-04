"""
recommender.py
--------------

Rule-based property recommendation engine.

This module recommends properties using structured data
stored in the SQLite database.

Recommendations are based on:

- Budget
- City
- Area
- Bedrooms
- Purpose
- Investment goals
"""
from collections import defaultdict
from database.sql_retriever import SQLRetriever


class PropertyRecommender:
    """
    Rule-based property recommendation engine.
    """

    def __init__(self):

        self.sql = SQLRetriever()

    # --------------------------------------------------
    # Load Properties
    # --------------------------------------------------

    def get_all_properties(self):
        """
        Load all properties from the database.
        """

        return self.sql._query(
            """
            SELECT *
            FROM properties
            """
        )

    # --------------------------------------------------
    # Load Amenities
    # --------------------------------------------------

    def get_property_amenities(self):
        """
        Build a mapping from property_id
        to a list of amenities.
        """

        rows = self.sql.get_amenities()

        amenities = defaultdict(list)

        for row in rows:
            amenities[row["property_id"]].append(
                row["amenity_name"].lower()
            )

        return amenities

    # --------------------------------------------------
    # Budget Filter
    # --------------------------------------------------

    def filter_budget(
        self,
        properties,
        budget,
    ):
        """
        Keep properties whose minimum price
        is within the user's budget.
        """

        return [
            p
            for p in properties
            if p["price_range_min_pkr"] <= budget
        ]

    # --------------------------------------------------
    # City Filter
    # --------------------------------------------------

    def filter_city(
        self,
        properties,
        city,
    ):
        """
        Keep properties in the selected city.
        """

        return [
            p
            for p in properties
            if p["city"].lower() == city.lower()
        ]

    # --------------------------------------------------
    # Area Filter
    # --------------------------------------------------

    def filter_area(
        self,
        properties,
        area,
    ):
        """
        Keep properties matching the selected area.
        """

        return [
            p
            for p in properties
            if area.lower() in p["area"].lower()
        ]

    # --------------------------------------------------
    # Bedroom Filter
    # --------------------------------------------------

    def filter_bedrooms(
        self,
        properties,
        bedrooms,
    ):
        """
        Keep properties offering the required
        number of bedrooms.
        """

        keyword = f"{bedrooms} Bed"

        return [
            p
            for p in properties
            if keyword.lower() in p["unit_types"].lower()
        ]

    # --------------------------------------------------
    # Property Type Filter
    # --------------------------------------------------

    def filter_purpose(
            self,
            properties,
            purpose,
        ):
            """
            Filter properties based on the user's purpose.
            """

            purpose = purpose.lower()

            residential_keywords = [
                "apartment",
                "villa",
                "house",
                "plot",
                "residential",
            ]

            commercial_keywords = [
                "commercial",
                "office",
                "shop",
                "business",
                "plaza",
            ]

            filtered = []

            for property_ in properties:

                property_type = property_["property_type"].lower()

                if purpose == "residential":

                    if any(
                        keyword in property_type
                        for keyword in residential_keywords
                    ):
                        filtered.append(property_)

                elif purpose == "commercial":

                    if any(
                        keyword in property_type
                        for keyword in commercial_keywords
                    ):
                        filtered.append(property_)

                else:

                    if purpose in property_type:
                        filtered.append(property_)

            return filtered

    # --------------------------------------------------
    # Amenity Filter
    # --------------------------------------------------

    def filter_amenities(
        self,
        properties,
        amenities,
    ):
        """
        Keep properties containing all
        requested amenities.
        """

        property_amenities = self.get_property_amenities()

        requested = [
            amenity.lower()
            for amenity in amenities
        ]

        filtered = []

        for property_ in properties:

            available = property_amenities.get(
                property_["property_id"],
                [],
            )

            if all(

                any(
                    requested_amenity in stored_amenity
                    for stored_amenity in available
                )

                for requested_amenity in requested
            ):

                filtered.append(property_)

        return filtered


    # --------------------------------------------------
    # Investment Goal Filter
    # --------------------------------------------------

    def filter_investment_goal(
        self,
        properties,
        goal,
    ):
        """
        Recommend under-construction properties
        for investment.
        """

        if goal.lower() != "investment":
            return properties

        return [
            p
            for p in properties
            if "under" in p["status"].lower()
        ]

    # --------------------------------------------------
    # Recommendation Engine
    # --------------------------------------------------

    def recommend(
        self,
        budget=None,
        city=None,
        area=None,
        bedrooms=None,
        purpose=None,
        amenities=None,
        investment_goal=None,
    ):
        """
        Recommend properties matching
        the supplied filters.
        """

        properties = self.get_all_properties()

        if budget is not None:
            properties = self.filter_budget(
                properties,
                budget,
            )

        if city:
            properties = self.filter_city(
                properties,
                city,
            )

        if area:
            properties = self.filter_area(
                properties,
                area,
            )

        if bedrooms:
            properties = self.filter_bedrooms(
                properties,
                bedrooms,
            )

        if purpose:
            properties = self.filter_purpose(
                properties,
                purpose,
            )

        if amenities:
            properties = self.filter_amenities(
                properties,
                amenities,
            )

        if investment_goal:
            properties = self.filter_investment_goal(
                properties,
                investment_goal,
            )

        return properties