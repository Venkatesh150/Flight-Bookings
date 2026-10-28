import unittest
from datetime import date, timedelta

import app


class FlightSearchTests(unittest.TestCase):
    def setUp(self):
        app.FLIGHTS.clear()

    def test_search_returns_three_sorted_flights(self):
        travel_date = (date.today() + timedelta(days=14)).isoformat()
        result, status = app.search_flights({
            "from": ["New York"],
            "to": ["Lisbon"],
            "date": [travel_date],
            "passengers": ["2"],
        })

        self.assertEqual(status, 200)
        self.assertEqual(len(result["flights"]), 3)
        self.assertEqual(
            [flight["price"] for flight in result["flights"]],
            sorted(flight["price"] for flight in result["flights"]),
        )
        self.assertTrue(all(flight["passengers"] == 2 for flight in result["flights"]))

    def test_search_rejects_same_city(self):
        result, status = app.search_flights({
            "from": ["Paris"],
            "to": ["Paris"],
            "date": [(date.today() + timedelta(days=1)).isoformat()],
            "passengers": ["1"],
        })

        self.assertEqual(status, 400)
        self.assertIn("different cities", result["error"])

    def test_search_rejects_past_date(self):
        result, status = app.search_flights({
            "from": ["New York"],
            "to": ["London"],
            "date": ["2000-01-01"],
            "passengers": ["1"],
        })

        self.assertEqual(status, 400)
        self.assertIn("today or later", result["error"])

    def test_booking_requires_a_searched_flight_and_valid_details(self):
        result, status = app.create_booking({"flightId": "missing", "name": "Alex", "email": "alex@example.com"})
        self.assertEqual(status, 404)

        travel_date = (date.today() + timedelta(days=14)).isoformat()
        search, _ = app.search_flights({
            "from": ["New York"], "to": ["Lisbon"], "date": [travel_date], "passengers": ["1"],
        })
        flight = search["flights"][0]
        result, status = app.create_booking({
            "flightId": flight["id"], "name": "Alex Morgan", "email": "alex@example.com",
        })

        self.assertEqual(status, 201)
        self.assertEqual(result["booking"]["flight"]["id"], flight["id"])
        self.assertEqual(len(result["booking"]["reference"]), 6)

    def test_concierge_handles_destination_and_fare_questions(self):
        self.assertIn("Lisbon", app.concierge_reply("Where should I go?"))
        self.assertIn("midweek", app.concierge_reply("How do I find a cheap fare?"))


if __name__ == "__main__":
    unittest.main()
