"""
test_recommender.py
-------------------

Standalone test for the
Property Recommendation Engine.

Run:

python test_recommender.py
"""

from database.database import PropertyDatabase
from app.recommendation.recommender import PropertyRecommender


def show_results(results,recommender):

    if not results:

        print("No matching properties found.\n")
        return

    for i, property_ in enumerate(results, start=1):

        print("-" * 70)

        print(f"Recommendation {i}")

        print(f"Project : {property_['project_name']}")
        print(f"City    : {property_['city']}")
        print(f"Area    : {property_['area']}")
        print(f"Type    : {property_['property_type']}")
        print(f"Status  : {property_['status']}")

        print(
            f"Price   : "
            f"PKR {property_['price_range_min_pkr']:,}"
            f" - "
            f"PKR {property_['price_range_max_pkr']:,}"
        )

        print(f"Units   : {property_['unit_types']}")
        amenities = recommender.get_property_amenities().get(
            property_["property_id"],
            [],
        )

        if amenities:
            print(
                "Amenities:",
                ", ".join(amenities),
            )
    print()


def main():

    print("=" * 70)
    print("PROPERTY RECOMMENDATION ENGINE")
    print("=" * 70)

    print("\nBuilding database...\n")

    db = PropertyDatabase()
    db.build_database()

    recommender = PropertyRecommender()

    # -------------------------------------------------

    print("\nTest 1")
    print("Budget = 30 Million")
    print("City = Lahore")
    print("Bedrooms = 3")

    results = recommender.recommend(
        budget=30000000,
        city="Lahore",
        bedrooms=3,
    )

    show_results(results,recommender,)

    # -------------------------------------------------

    print("\nTest 2")
    print("Budget = 50 Million")
    print("City = Islamabad")

    results = recommender.recommend(
        budget=50000000,
        city="Islamabad",
    )

    show_results(results,recommender,)

    # -------------------------------------------------

    print("\nTest 3")
    print("City = Karachi")
    print("Purpose = Commercial")

    results = recommender.recommend(
        city="Karachi",
        purpose="Commercial",
    )

    show_results(results,recommender,)

    # -------------------------------------------------

    print("\nTest 4")
    print("Investment Properties")

    results = recommender.recommend(
        investment_goal="investment",
    )

    show_results(results,recommender,)

    # -------------------------------------------------

    print("\nTest 5")
    print("Lahore properties with Gym and Swimming Pool")

    results = recommender.recommend(
        city="Lahore",
        amenities=[
            "Gymnasium",
            "Pool",
        ],
    )

    show_results(results,recommender,)


if __name__ == "__main__":
    main()