# Self-Hosted S3 Gateway

Garage-backed S3-compatible storage gateway with a small authenticated FastAPI
surface for object CRUD.

> Status: early development. APIs, config, and deployment flow may change before v1.

## Local Tests

From the backend directory:

```bash
cd backend
python -m pip install -e ".[dev]"
pytest
```

The fast test suite stubs the S3 client, so it does not require Docker or a
running Garage node.

## Run Garage + Backend

The repo includes local development credentials in `.env` and
`garage/garage.toml` so CRUD can be tested immediately. Replace them before
using this on any real network.

```bash
docker compose up -d --build
```

Check the backend:

```bash
curl http://localhost:8000/healthz
```

Upload, list, download, and delete an object:

```bash
curl -sS -H "X-API-Key: dev-api-key-change-me" \
  -F "key=test/hello.txt" \
  -F "file=@README.md;type=text/plain" \
  http://localhost:8000/api/objects

curl -sS -H "X-API-Key: dev-api-key-change-me" \
  "http://localhost:8000/api/objects?prefix=test/"

curl -sS -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/objects/test/hello.txt

curl -sS -X DELETE -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/objects/test/hello.txt
```

## Regenerate Garage Secrets

For a fresh local config, remove `garage/garage.toml`, then run:

```bash
./init_garage_config.sh
```

Copy `.env.example` to `.env` and set matching
`GARAGE_DEFAULT_ACCESS_KEY` / `S3_ACCESS_KEY` and
`GARAGE_DEFAULT_SECRET_KEY` / `S3_SECRET_KEY` values.
