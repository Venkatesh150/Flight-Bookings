from __future__ import annotations

import json
import os
import re
import secrets
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent
AIRPORTS = {
    "New York": {"code": "JFK", "country": "United States"},
    "London": {"code": "LHR", "country": "United Kingdom"},
    "Paris": {"code": "CDG", "country": "France"},
    "Tokyo": {"code": "HND", "country": "Japan"},
    "Singapore": {"code": "SIN", "country": "Singapore"},
    "Dubai": {"code": "DXB", "country": "United Arab Emirates"},
    "Lisbon": {"code": "LIS", "country": "Portugal"},
    "Reykjavik": {"code": "KEF", "country": "Iceland"},
    "Cape Town": {"code": "CPT", "country": "South Africa"},
    "Bali": {"code": "DPS", "country": "Indonesia"},
}
AIRLINES = [
    {"name": "Northstar Air", "mark": "N", "color": "#3157d5"},
    {"name": "Ember Airways", "mark": "E", "color": "#ec7656"},
    {"name": "Cloudline", "mark": "C", "color": "#31a890"},
]

# Demo bookings and searched flights live in memory and reset when the server restarts.
FLIGHTS: dict[str, dict] = {}
BOOKINGS: list[dict] = []


def json_bytes(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def search_flights(query: dict[str, list[str]]) -> tuple[dict, int]:
    origin = query.get("from", [""])[0].strip()
    destination = query.get("to", [""])[0].strip()
    travel_date = query.get("date", [""])[0].strip()
    passengers_raw = query.get("passengers", ["1"])[0]

    if origin not in AIRPORTS or destination not in AIRPORTS:
        return {"error": "Choose a departure and arrival city from the list."}, 400
    if origin == destination:
        return {"error": "Choose two different cities for your trip."}, 400
    try:
        parsed_date = date.fromisoformat(travel_date)
    except ValueError:
        return {"error": "Choose a valid departure date."}, 400
    if parsed_date < date.today():
        return {"error": "Departure date must be today or later."}, 400
    if not re.fullmatch(r"\d{1,2}", passengers_raw):
        return {"error": "Passenger count must be between 1 and 9."}, 400
    passengers = int(passengers_raw)
    if not 1 <= passengers <= 9:
        return {"error": "Passenger count must be between 1 and 9."}, 400

    start_minutes = 390 + (sum(map(ord, origin + destination)) % 360)
    base_fare = 245 + (sum(map(ord, origin + destination + travel_date)) % 340)
    durations = [7 * 60 + 35, 8 * 60 + 20, 9 * 60 + 5]
    flights = []
    for index, airline in enumerate(AIRLINES):
        departure_minutes = (start_minutes + index * 115) % (24 * 60)
        arrival_minutes = (departure_minutes + durations[index]) % (24 * 60)
        flight = {
            "id": f"{AIRPORTS[origin]['code']}-{AIRPORTS[destination]['code']}-{travel_date}-{index}",
            "airline": airline["name"],
            "mark": airline["mark"],
            "color": airline["color"],
            "from": origin,
            "to": destination,
            "fromCode": AIRPORTS[origin]["code"],
            "toCode": AIRPORTS[destination]["code"],
            "date": travel_date,
            "depart": f"{departure_minutes // 60:02d}:{departure_minutes % 60:02d}",
            "arrive": f"{arrival_minutes // 60:02d}:{arrival_minutes % 60:02d}",
            "duration": f"{durations[index] // 60}h {durations[index] % 60:02d}m",
            "stops": "Nonstop" if index == 0 else ("1 stop" if index == 1 else "Nonstop"),
            "price": base_fare + index * 67,
            "passengers": passengers,
        }
        FLIGHTS[flight["id"]] = flight
        flights.append(flight)

    flights.sort(key=lambda result: result["price"])
    return {"flights": flights, "route": {"from": origin, "to": destination, "date": travel_date}}, 200


def create_booking(payload: dict) -> tuple[dict, int]:
    flight_id = str(payload.get("flightId", ""))
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    flight = FLIGHTS.get(flight_id)

    if not flight:
        return {"error": "That flight is no longer available. Search again to refresh results."}, 404
    if len(name) < 2 or len(name) > 80:
        return {"error": "Enter a name between 2 and 80 characters."}, 400
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return {"error": "Enter a valid email address."}, 400

    booking = {
        "reference": secrets.token_hex(3).upper(),
        "name": name,
        "email": email,
        "flight": flight,
    }
    BOOKINGS.append(booking)
    return {"booking": booking}, 201


def concierge_reply(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("cheapest", "cheap", "price", "deal", "budget", "cost")):
        return (
            "For a better fare, try flying midweek, booking a few weeks ahead, and comparing "
            "nearby dates. I can show three sample fares at once—choose your cities and search "
            "to see the lowest option."
        )
    if any(word in text for word in ("book", "booking", "reserve", "ticket")):
        return (
            "I can help you find a ticket. Search a route first, then choose a flight and enter "
            "your passenger details to create a demo booking. Your confirmation appears right here."
        )
    if any(word in text for word in ("destination", "where", "recommend", "recommendation", "trip")):
        return (
            "For a little inspiration: Lisbon has golden-hour viewpoints, Reykjavik is a gateway "
            "to the northern lights, and Cape Town pairs dramatic coastlines with mountain trails. "
            "Pick one in the search form and let’s explore."
        )
    if any(word in text for word in ("hello", "hi", "hey")):
        return (
            "Hi, I’m your Wayfarer trip concierge. Ask me about destinations, finding a better "
            "fare, or how to book your flight."
        )
    return (
        "I’m your Wayfarer trip concierge. I can suggest destinations, share fare-finding "
        "tips, and walk you through a demo booking. What kind of trip are you dreaming of?"
    )


class WayfarerHandler(BaseHTTPRequestHandler):
    server_version = "WayfarerDemo/1.0"

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, body: dict) -> None:
        self.send_bytes(status, json_bytes(body), "application/json; charset=utf-8")

    def read_json(self) -> dict | None:
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdigit() or int(raw_length) > 16_384:
            return None
        try:
            payload = json.loads(self.rfile.read(int(raw_length)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(200, (ROOT / "templates" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif parsed.path == "/api/airports":
            airports = [{"city": city, **details} for city, details in AIRPORTS.items()]
            self.send_bytes(200, json_bytes(airports), "application/json; charset=utf-8")
        elif parsed.path == "/api/flights":
            result, status = search_flights(parse_qs(parsed.query))
            self.send_json(status, result)
        elif parsed.path in ("/static/style.css", "/static/app.js"):
            asset = ROOT / unquote(parsed.path).lstrip("/")
            content_type = "text/css; charset=utf-8" if asset.suffix == ".css" else "text/javascript; charset=utf-8"
            self.send_bytes(200, asset.read_bytes(), content_type)
        else:
            self.send_json(404, {"error": "Page not found."})

    def do_POST(self) -> None:
        payload = self.read_json()
        if payload is None:
            self.send_json(400, {"error": "Send a valid JSON object under 16 KB."})
            return
        if self.path == "/api/bookings":
            result, status = create_booking(payload)
            self.send_json(status, result)
        elif self.path == "/api/concierge":
            message = str(payload.get("message", "")).strip()
            if not message or len(message) > 500:
                self.send_json(400, {"error": "Send a message of 1–500 characters."})
                return
            self.send_json(200, {"reply": concierge_reply(message)})
        else:
            self.send_json(404, {"error": "Page not found."})

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    server = ThreadingHTTPServer((host, port), WayfarerHandler)
    print(f"Wayfarer is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Wayfarer.")
    finally:
        server.server_close()
