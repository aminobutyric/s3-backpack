# S3 Backpack Product Design Document

Status: v0.2 product prototype
Last updated: 2026-07-22

## 1. Problem & Pitch

Self-hosters and small technical teams need an understandable way to keep a
verified copy of cloud object data under their physical control. Existing tools
can perform the transfer, but safely selecting a removable disk, provisioning a
local S3 target, verifying a run, restoring data, and ejecting the disk still
requires a collection of commands and operational knowledge.

**S3 Backpack pitch:** *A verified, portable local mirror of your cloud S3 data.*

## 2. Target Persona

Primary: self-hosters, homelab operators, and small data teams running on modest
hardware who want an offline copy, a cloud exit path, or a physically portable
dataset. They evaluate tools by:
- No lock-in, no phone-home
- Low resource footprint
- Config-as-code (docker-compose + `.env`), not wizard-only
- Boring, inspectable internals (standard S3 API, readable logs)
- Real docs (architecture, tradeoffs), not marketing copy
- Contribution-friendly (permissive license, clear CONTRIBUTING.md, good-first-issues)

Not the initial target: non-technical "prosumer with a NAS" users. May become a secondary audience later via a hosted tier, not in v1.

## 3. Core Differentiator And Hook

- **Differentiator:** rclone supplies proven transfer behavior and Garage supplies
  the local S3 endpoint. S3 Backpack supplies the safety workflow around them:
  disk identity, mount guards, capacity checks, non-destructive defaults,
  verification reports, recovery instructions, and safe eject.
- **Hook:** copy a cloud bucket to a disk, disconnect the network, and retrieve
  the same objects from a local S3 endpoint.
- **Trust boundary:** no formatting, deletion, destructive mirroring, or restore
  overwrite occurs without a preview and explicit confirmation.

## 4. Architecture Overview

Four components have distinct ownership:

1. **Cloud S3 source** - AWS, R2, B2, Wasabi, or another S3-compatible service.
2. **rclone transfer engine** - copies and verifies data using named remotes.
3. **Garage local target** - receives objects through its S3 API and stores its
   complete metadata and data state on the selected attached disk.
4. **S3 Backpack control plane** - validates disks, plans jobs, invokes rclone,
   records results, exposes progress, and coordinates safe startup and shutdown.

The data path is always `cloud S3 -> rclone -> Garage S3 API`. Rclone and S3
Backpack must never write directly into Garage's metadata or data directories.

### Storage source note (Garage)
Garage doesn't mount a drive as S3 directly — it owns a data directory pointed at a mounted volume/path and exposes an S3-compatible API in front of it. Any Docker-mountable volume works: internal disk, external USB/HDD, NFS/SMB share, etc.

## 5. v0.2 Scope

- Linux block-device discovery using stable device identifiers
- Read-only inspection before any storage action
- Mount verification and protection against writes to an unmounted host path
- Garage metadata and object data located together on the selected disk
- Named cloud and local rclone remotes
- Source bucket/prefix selection and capacity preflight
- Non-destructive backup using `rclone copy`
- One-way post-transfer verification using `rclone check`
- Progress, cancellation, structured logs, and a durable transfer manifest
- Local object browsing and S3 endpoint credentials
- Non-destructive restore from the Backpack disk to cloud S3
- Coordinated Garage shutdown and safe disk eject

## 6. Safety Invariants

- A transfer is bound to the selected disk UUID, not only a mount path.
- Backup mode never deletes destination objects.
- Mirror mode is out of v0.2; it will require a dry-run deletion preview.
- Restore never deletes cloud objects by default.
- A failed or incomplete verification is visible and cannot be reported as a
  successful backup.
- Formatting is out of v0.2. Existing supported filesystems are used as-is.
- The first release does not claim to preserve bucket IAM, lifecycle rules,
  object versions, legal holds, or every provider-specific metadata field.
- Replicated buckets preserve object bytes and keys; content transformation is
  disabled in the replication path.

## 7. Stack Decisions

- **Language: Python throughout** (not a Go/Rust polyglot split) — avoids two-runtime deployment complexity and contribution friction; matches your own strength; can extract a hot path to Go/Rust later only if profiling proves a genuine bottleneck.
- **Framework: FastAPI** — async-first, typed, signals rigor to the Go/Rust-literate audience without leaving Python.
- **Type hints throughout**, clean mypy/pyright.
- **Compiled libraries for heavy lifting** on the compression path (e.g. `zstandard`, `libvips` bindings) — near-native speed on the hot path without a second language.
- **Web UI: htmx + Jinja2 (or vanilla JS + FastAPI static files), not React.** Matches the persona's preference for inspectable internals (open DevTools, understand what's happening) and keeps bundle size small enough to be comfortable on a Pi; also avoids a separate JS build pipeline in an otherwise Python-only stack.

## 8. Licensing / Distribution Model

**Open core.**
- **Free/OSS core:** abstraction layer, self-hosted Garage integration, basic compression, local web UI. Permissive license (MIT/Apache — not BSL, which self-hosters distrust).
- **Paid (later, not v1):** optional hosted version, advanced features (managed key recovery for encryption, multi-backend tiering, team/multi-user access).

## 9. Current Product Decisions

- Product name: **S3 Backpack**
- Product stage: v0.2 prototype; no stable release has been made
- Core workflow: cloud S3 to a verified Garage mirror on an attached disk
- Transfer engine: rclone, invoked through structured arguments without a shell
- Default transfer semantics: one-way, non-destructive copy
- Existing compression work remains experimental and is not used for mirrors
- Documentation structure: README plus architecture, design, progress, and contribution documents under `docs/`
