# S3 Backpack

[![Backend CI](https://github.com/aminobutyric/s3-backpack/actions/workflows/backend-tests.yml/badge.svg?branch=develop)](https://github.com/aminobutyric/s3-backpack/actions/workflows/backend-tests.yml)

Garage-backed S3-compatible storage gateway with a small authenticated FastAPI
surface for object CRUD.

> **Status:** v0.2 design and foundation prototype. The end-to-end portable
> mirror and restore workflow is not implemented yet. The earlier v1 scope was
> withdrawn before a stable release.

S3 Backpack is being developed to copy selected cloud S3 buckets onto an
attached disk, verify the copy, and serve it through a local Garage S3 endpoint.
The intended result is a portable cloud exit and offline recovery path rather
than another general-purpose object browser.

```text
Cloud S3 -> rclone -> local Garage -> attached Backpack disk
```

## Available Now

- Garage-backed upload, list, download, existence-check, and delete operations
- API-key-protected FastAPI endpoints and a small object-management web UI
- Content-aware zstd and WebP compression experiments
- Transparent zstd decompression for objects uploaded through the gateway
- A typed, shell-free rclone `copy` and `check` command layer with unit tests
- Read-only Linux `lsblk` inventory and system-disk classification
- Docker Compose development stack, pytest coverage, mypy, and GitHub Actions

## Planned For v0.2

- Trustworthy host-disk inventory inside the Docker deployment
- Disk selection, UUID binding, mount guards, and capacity preflight
- Placement of Garage metadata and object data on the selected disk
- Cloud S3 remote setup and bucket/prefix selection
- Asynchronous rclone jobs with progress and cancellation
- Durable transfer and verification reports
- Non-destructive restore workflow
- Coordinated Garage shutdown and safe disk eject

Until those items are complete, S3 Backpack should be treated as a development
foundation and CRUD gateway, not as a working cloud-to-disk backup product.

> [!WARNING]
> The example credentials are public, development-only values. Never expose this
> stack to a LAN, the internet, or real data while using them. Generate unique
> Garage RPC/admin secrets, S3 credentials, and `API_KEY` before any non-local
> deployment. Do not commit the generated `.env` or `garage/garage.toml` files.

## Local Tests

From the backend directory:

```bash
cd backend
python -m pip install -e ".[dev]"
pytest
```

The fast test suite stubs the S3 client, so it does not require Docker or a
running Garage node.

GitHub Actions runs pytest, mypy, builds the backend image, and verifies the
pinned rclone binary. See
[`.github/workflows/backend-tests.yml`](.github/workflows/backend-tests.yml).

## Run Garage + Backend

Local development uses ignored `.env` and `garage/garage.toml` files. The
tracked example files contain intentionally public development values. Generate
or replace them before starting the stack, and never use those values on a real
network.

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
