# Ecoharmonogram Standalone API

Minimal API wrapper around `ecoharmonogram.pl` 

## Run with Docker Compose

```bash
docker compose up --build -d
```

Server starts at `http://127.0.0.1:8000`.

Stop:

```bash
docker compose down
```

## Run with Docker only

```bash
docker build -t ecoharmonogram-api .
docker run --rm -p 8000:8000 --name ecoharmonogram-api ecoharmonogram-api
```

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server starts at `http://127.0.0.1:8000`.

## Endpoints

- `GET /health` — health check.
- `POST /towns` — lookup towns (`getTowns` / `getTownsForCommunity`).
- `POST /schedule` — resolve all collection dates and waste types for an address.

## Example: schedule request

```bash
curl -X POST http://127.0.0.1:8000/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "town": "Częstochowa",
    "street": "Bartnicza",
    "house_number": "9",
    "district": "Częstochowa",
    "additional_sides_matcher": "Szkło (1 x miesiąc)",
    "g1": "Firmy (5 fakcji + popiół 2,3,4 x mc)",
    "g2": "Zmieszane (5 x miesiąc)",
    "g3": "Bio (3 x miesiąc)",
    "g4": "Metale i Tworzywa (4 x miesiąc)",
    "g5": "Papier (1 x miesiąc)"
  }'
```

## Response format

```json
{
  "count": 42,
  "entries": [
    { "date": "2026-01-03", "type": "Papier" }
  ]
}
```