# S3 Backpack

Garage-backed S3-compatible storage gateway with a small authenticated FastAPI
surface for object CRUD.

> Status: v1 scope finalized. The project is preparing for its first stable release.

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

Open `http://localhost:8000` for the web UI. Enter the value of `API_KEY`
from `.env`; it is kept in browser session storage for the current tab and is
sent to the backend as the `X-API-Key` header.

Upload, list, download, and delete an object:

```bash
curl -sS -H "X-API-Key: dev-api-key-change-me" \
  -F "key=test/hello.txt" \
  -F "file=@README.md;type=text/plain" \
  http://localhost:8000/api/objects

curl -sS -H "X-API-Key: dev-api-key-change-me" \
  "http://localhost:8000/api/objects?prefix=test/"

curl -sS -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/objects/test/hello.txt.zst \
  --output /tmp/hello.txt

curl -sS -X DELETE -H "X-API-Key: dev-api-key-change-me" \
  http://localhost:8000/api/objects/test/hello.txt.zst
```

The upload response contains the actual stored key. Compressible text and log
files are stored with a `.zst` suffix; PNG, BMP, and TIFF images are stored with
a `.webp` suffix. A transformation is used only when its output is smaller.
Already-compressed formats such as ZIP, gzip, MP4, JPEG, WebP, and zstd are
stored unchanged.

Garage and direct S3 clients see transformed objects in their stored format.
Downloads through the gateway API and web UI transparently decompress zstd
objects created by the gateway and restore their original filename and content
type. Legacy `.zst` objects without gateway metadata are returned unchanged.
WebP conversions remain WebP because that image conversion is lossy.

The API documents its request and response schemas at
`http://localhost:8000/docs`.

## Regenerate Garage Secrets

For a fresh local config, remove `garage/garage.toml`, then run:

```bash
./init_garage_config.sh
```

Copy `.env.example` to `.env` and set matching
`GARAGE_DEFAULT_ACCESS_KEY` / `S3_ACCESS_KEY` and
`GARAGE_DEFAULT_SECRET_KEY` / `S3_SECRET_KEY` values.
