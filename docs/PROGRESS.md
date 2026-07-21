# Product Checklist

## v1

[x] Storage abstraction interface

[x] Garage S3-compatible backend

[x] Upload, list, download, existence check, and delete operations

[x] Required API-key authentication

[x] Text/log compression using zstd level 3

[x] PNG/BMP/TIFF conversion to WebP quality 85

[x] Skip-list for already-compressed formats

[x] Skip compression when output would be larger

[x] Preserve original when image decoding fails

[x] Return actual transformed `.zst` or `.webp` key

[x] Web UI using Jinja2 and dependency-free JavaScript

[x] GUI upload, browse, prefix filtering, download, and confirmed delete

[x] API key stored only for the browser tab

[x] Docker Compose deployment

[x] Configuration through `.env`

[x] Garage integration and CRUD tests

[x] Compression and UI tests

[x] README, architecture, design, and contribution documentation

[x] Permissive license

[x] Type hints enforced with mypy locally and in CI

[x] Transparent zstd decompression on gateway download

[x] Correct stored content type and filename metadata on download

[x] Finalize v1 scope and remove draft status

[x] Final product name and branding: S3 Backpack

## v1.1

Cloud S3 backend

Validate that backend switching is configuration-only

## v1.2

Linux USB/external-drive detection

Garage data-directory configuration for detected drives

Filesystem inspection

XFS recommendation flow

Explicitly confirmed formatting

Protection against formatting drives containing data

## v2+ Backlog

Hosted/SaaS tier

Multi-tenancy and billing

Client-side zero-knowledge encryption

Watched-folder synchronization

Multi-backend mirroring and storage tiering

Deduplication

AI cleanup/archive assistant with confirmation

Expiring share links

Multiple managed API keys and access tokens
