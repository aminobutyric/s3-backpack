# Contributing

## Development Setup

```bash
cd backend
python -m pip install -e ".[dev]"
python -m pytest
python -m mypy app
```

The default tests cover the Garage storage wrapper with botocore stubs and the
FastAPI CRUD routes with an in-memory storage backend. Real Garage integration
tests run only when `S3_ACCESS_KEY` and `S3_SECRET_KEY` are exported.

## Real Garage CRUD Test

```bash
docker compose up -d garage
cd backend
export $(grep -v '^#' ../.env | xargs)
pytest tests/test_storage_garage.py
```

Keep route code provider-agnostic: API modules should depend on
`StorageBackend`, not on `GarageBackend` directly.


## Future contributor workflow should use short-lived branches from develop:
```bash
git switch develop
git pull --ff-only
git switch -c feature/transparent-downloads
```
