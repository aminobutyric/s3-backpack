s3-gateway/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py               # env-based config
│   │   ├── web.py                  # server-rendered web UI entrypoint
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
│   │   │   └── garage.py           # only implementation in v1
│   │   ├── compression/
│   │   │   ├── __init__.py
│   │   │   ├── images.py           # WebP, quality 85
│   │   │   ├── text.py             # zstd, level 3
│   │   │   └── skiplist.py         # .zip, .gz, .mp4, .jpg, etc.
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py          # typed request/response models
│   ├── templates/                  # Jinja2 templates (htmx)
│   │   ├── base.html
│   │   ├── browse.html
│   │   └── upload.html
│   ├── static/                     # dependency-free browser CSS/JS
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
