# Product Checklist

Status: v0.2 prototype. The withdrawn `v1.0.0` tag did not represent a stable
release and is no longer published.

## Prototype Foundation

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

[x] Product name and branding: S3 Backpack

## v0.2 Portable Mirror

[x] Define cloud S3 to rclone to Garage data flow

[x] Define non-destructive backup and restore defaults

[x] Typed rclone command and execution layer

[x] Read-only Linux block-device discovery and classification

[x] Stable disk identity using filesystem UUID

[x] Whole-system-disk rejection based on child mountpoints

[ ] Least-privilege host inventory bridge for Docker

[ ] Read-only filesystem and capacity inspection

[ ] Protection against an absent or incorrectly mounted target disk

[ ] Garage metadata and data placement on the selected disk

[ ] Cloud S3 remote configuration

[ ] Source bucket and prefix selection

[ ] Capacity preflight

[ ] Asynchronous backup jobs with progress and cancellation

[x] One-way post-copy verification foundation

[ ] Durable JSON transfer manifests

[ ] Restore workflow

[ ] Safe Garage shutdown and disk eject

[ ] End-to-end test with a real S3-compatible cloud source

[ ] Move product status from prototype to release candidate

## Later Backlog

Hosted/SaaS tier

Multi-tenancy and billing

Client-side zero-knowledge encryption

Watched-folder synchronization

Explicit mirror mode with deletion preview

Bidirectional synchronization

S3 version-history backup

Bucket IAM, lifecycle, retention, and legal-hold replication

Multi-backend mirroring and storage tiering

Deduplication

AI cleanup/archive assistant with confirmation

Expiring share links

Multiple managed API keys and access tokens
