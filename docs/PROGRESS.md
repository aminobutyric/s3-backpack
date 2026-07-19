# Product Checklist

## v1

Storage abstraction interface

Garage S3-compatible backend

Upload, list, download, existence check, and delete operations

Required API-key authentication

Text/log compression using zstd level 3

PNG/BMP/TIFF conversion to WebP quality 85

Skip-list for already-compressed formats

Skip compression when output would be larger

Preserve original when image decoding fails

Return actual transformed .zst or .webp key

Web UI using Jinja2 and dependency-free JavaScript

GUI upload, browse, prefix filtering, download, and confirmed delete

API key stored only for the browser tab

Docker Compose deployment

Configuration through .env

Garage integration and CRUD tests

Compression and UI tests

README, architecture, design, and contribution documentation

Permissive license
[~] Type hints are present, but no mypy/pyright enforcement yet

Transparent zstd decompression on download

Correct stored content type and filename metadata on download

Finalize v1 scope and remove “draft” status

Final product name and branding

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