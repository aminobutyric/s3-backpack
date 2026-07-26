s3-backpack/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py               # env-based config
│   │   ├── ui/
│   │   │   └── routes.py           # server-rendered web UI entrypoint
│   │   ├── templates/               # Jinja2 UI templates
│   │   │   ├── base.html
│   │   │   ├── browse.html
│   │   │   └── upload.html
│   │   ├── static/                  # dependency-free browser CSS/JS
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── api_key.py          # API key generation/validation
│   │   │   └── dependencies.py     # FastAPI auth dependency for routes
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py
│   │   │   ├── browse.py
│   │   │   └── delete.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # StorageBackend interface
│   │   │   └── garage.py           # local S3 target
│   │   ├── transfers/
│   │   │   └── rclone.py            # safe copy/check command boundary
│   │   ├── compression/
│   │   │   ├── __init__.py
│   │   │   ├── images.py           # WebP, quality 85
│   │   │   ├── text.py             # zstd, level 3
│   │   │   └── skiplist.py         # .zip, .gz, .mp4, .jpg, etc.
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py          # typed request/response models
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_storage_garage.py
│   │   ├── test_compression.py
│   │   └── test_auth.py
│   ├── pyproject.toml
│   └── Dockerfile
├── garage/
│   └── garage.toml                 # Garage node config
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   └── CONTRIBUTING.md
├── LICENSE                         # MIT or Apache
└── README.md

## Portable Mirror Data Flow

```text
cloud S3 remote
      |
      | rclone copy / check (S3 API)
      v
local Garage remote
      |
      v
selected attached disk
  - Garage metadata
  - Garage object data
  - S3 Backpack manifests
```

S3 Backpack is the control plane, rclone is the transfer engine, and Garage is
the local object server. Neither S3 Backpack nor rclone may write into Garage's
internal directories. All replicated objects enter and leave Garage through its
S3 API.

The first transfer operation is a non-destructive copy. Destructive mirror and
bidirectional modes are deliberately absent until deletion previews and durable
job recovery exist.

## Host Disk Boundary

Disk discovery is read-only and parses structured `lsblk` output. A device is
never considered ready unless it has a supported filesystem, a stable UUID, a
mountpoint, is writable, and does not share a physical parent with a system
mount such as `/`, `/boot`, or `/var`.

When running directly on Linux, the backend can read the host inventory. A
normal Docker container can see block topology but not trustworthy host
filesystem UUID and mount information, so discovery fails closed and reports no
ready disk. A least-privilege host inventory bridge is required before Docker
can select a disk. Raw host block devices must not be exposed to the web
container merely to make discovery work.
