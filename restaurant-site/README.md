# Sorella Restaurant Website

A responsive restaurant website built with ASP.NET Core Minimal APIs and a plain
HTML, CSS, and JavaScript frontend. It includes a filterable seasonal menu and a
working demo table-reservation form.

## Requirements

- .NET 8 SDK or later

## Run locally

From the repository root:

```bash
dotnet run --project restaurant-site/RestaurantSite.csproj
```

Open the URL printed by `dotnet run` (usually `http://localhost:5000` or
`https://localhost:5001`).

## API

- `GET /api/menu` — returns the sample menu.
- `POST /api/reservations` — validates and records a demo reservation in memory.

Reservations reset when the application restarts. The restaurant address, phone,
and menu are sample content; update them before using this as a real business site.
