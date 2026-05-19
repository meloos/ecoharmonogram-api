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

## Testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

## CI/CD

- CI workflow: .github/workflows/ci.yml
- Docker publish workflow: .github/workflows/docker-publish.yml
- Helm publish workflow: .github/workflows/helm-publish.yml

Behavior:

- Push or PR runs tests and syntax checks.
- Push to `main` publishes Docker image tags (`main`, `sha-*`, `latest`).
- Tag `v*` publishes Docker release tag and uploads Helm chart `.tgz` to the GitHub Release.

## Helm Chart

Chart location: helm/ecoharmonogram-api

Package locally:

```bash
helm package ./helm/ecoharmonogram-api
```

## Flux Example

Flux sample manifest:

- helm/FLUX-EXAMPLE.yaml

Note: The current Helm publish workflow uploads chart files to GitHub Releases (not OCI).
If you want Flux to pull charts as OCI artifacts, switch Helm publishing back to `helm push oci://...`.

## Release Flow

1. Update chart version in `helm/ecoharmonogram-api/Chart.yaml`.
2. Commit and push to `main`.
3. Create and push tag, for example:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

After tag push:

- Docker image is available at `ghcr.io/meloos/ecoharmonogram-api:v1.0.0`.
- Helm chart archive is attached to the GitHub Release as `ecoharmonogram-api-<version>.tgz`.