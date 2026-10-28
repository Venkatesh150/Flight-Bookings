# Wayfarer Flight Bookings

A polished, responsive flight-search demo built with Python's standard library. It includes
sample flight results, a demo booking flow, and a chat-based trip concierge.

## Run locally

```bash
python app.py
```

Requires Python 3.10 or later; there are no third-party dependencies.

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Run with Docker

Build the image from the project directory:

```bash
docker build -t wayfarer .
```

Start the container and publish its port:

```bash
docker run --rm -p 5000:5000 wayfarer
```

Open [http://localhost:5000](http://localhost:5000).

## What works

- Search sample one-way flights between 10 destinations.
- Swap routes, choose a travel date, and select up to nine travelers.
- View fares sorted by price and submit a demo booking.
- Chat with the trip concierge about destinations, booking, and fare tips.
- Responsive layouts for desktop and mobile.

## Demo limitations

Flight prices and schedules are illustrative, not live inventory. Bookings are held
in memory and disappear when the server restarts. The concierge uses lightweight
intent matching and does not connect to an external AI service. A production
booking service should connect verified airline inventory, persistent storage,
payment processing, and an AI provider.
