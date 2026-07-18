# Product Design Document — Self-Hosted / Portable S3 Gateway

Status: Draft v1
Last updated: 2026-07-18

## 1. Problem & Pitch

Self-hosters and technical users who work with object storage want a tool that lets them run their own S3-compatible storage anywhere Docker runs, without being locked into a single cloud provider — and without the storage bloat that comes from uploading files as-is.

**Pitch:** *Your own S3, anywhere, that also shrinks your files for you.*

## 2. Target Persona

Primary: self-hosters, homelab operators, and data engineers (the "OSS crowd") — technical users running things on modest hardware (Pi, old NAS, home server), who evaluate tools by:
- No lock-in, no phone-home
- Low resource footprint
- Config-as-code (docker-compose + `.env`), not wizard-only
- Boring, inspectable internals (standard S3 API, readable logs)
- Real docs (architecture, tradeoffs), not marketing copy
- Contribution-friendly (permissive license, clear CONTRIBUTING.md, good-first-issues)

Not the initial target: non-technical "prosumer with a NAS" users. May become a secondary audience later via a hosted tier, not in v1.

## 3. Core Differentiator & Hook

- **Moat (product, not architecture):** S3-compatible backend abstraction alone is table stakes in this space (MinIO, SeaweedFS, etc. all do it). The real moat is the *combination*: zero-config `docker-compose up` deployment + content-aware compression + trust-first UX (explicit confirmation on any destructive/autonomous action, no phone-home). No single piece is unique; the combination executed well for this persona is what's hard to copy.
- **Hook (why someone tries it):** intelligent, content-aware compression that visibly shrinks storage use on upload — demoable, satisfying, easy to show in 30 seconds.

Everything else (encryption, sync-folder, tiering, dedup) is a v2+ feature layered on top, not a competing differentiator.

## 4. Architecture Overview

Three-layer stack, with the key principle that layers only ever talk to each other over the S3 API — nothing is backend-specific outside layer 1:

1. **Storage backend** — either a real cloud S3 provider (AWS/Backblaze/etc.) or a self-hosted Garage instance, both speak the S3 API.
2. **Backend service** — talks S3 API to whichever backend is active; handles compression, metadata, auth. This is where the abstraction lives.
3. **Web UI** — upload/browse/manage; provider-agnostic because it only ever talks to the backend service.

Swapping cloud S3 for local Garage (or vice versa) should be a config change, not a code change.

### Storage source note (Garage)
Garage doesn't mount a drive as S3 directly — it owns a data directory pointed at a mounted volume/path and exposes an S3-compatible API in front of it. Any Docker-mountable volume works: internal disk, external USB/HDD, NFS/SMB share, etc.

## 5. Notable Features (beyond core CRUD)

- **USB/external drive auto-detect as storage source (v1.2, not core v1)** — Linux hosts only for v1 (Docker Desktop on Mac/Windows can't see host hotplug events). Detected drives can be used as a Garage storage backend.
- **XFS as recommended filesystem for the data partition** — confirmed via Garage's own documentation: XFS is recommended for performance; EXT4 is discouraged due to inode limits under large object counts.
- **Formatting is always an explicit, user-confirmed action — never automatic.** On detecting a drive: if empty/unformatted, offer to format as XFS with explicit confirmation; if it already has data or another filesystem, surface it as usable-but-not-optimal and let the user opt in to reformatting. Auto-formatting on detection is a hard no — destroys trust with this audience if it destroys data.
- **AI agent helper** — assists with cleanup (dedup/stale file detection), archiving (flagging cold files for tiering), and directory structure/naming suggestions (useful since S3 has no native folder concept). **Must propose, not act:** the agent generates a plan (what it would clean/archive/reorganize) and the user reviews and confirms before anything is moved or deleted. No silent autonomous action on user files — same trust boundary as the formatting flow, but ongoing rather than one-time, so it matters even more here.

## 6. MVP Scope (sequenced)

Previous draft stacked ~3 MVPs into one v1 (dual backend + drive detection + compression + UI all at once). Re-sequenced by real complexity/risk:

**v1 — true minimum:**
- Storage abstraction layer (`storage/base.py` interface)
- **One backend: self-hosted Garage only** (cloud S3 deferred — see v1.1)
- **Auth: API key or basic auth, required.** Not optional even for single-user self-hosting — undefended object storage on a network is a real vulnerability, not scope creep.
- Compression, with specific v1 rules (not just "content-aware"):
  - Images → WebP, quality 85
  - Text/logs → zstd, level 3
  - Skip-list (already compressed, don't touch): `.zip`, `.gz`, `.mp4`, `.jpg`
- Web UI: htmx + Jinja2 (or vanilla JS + FastAPI static files) — upload, browse, delete. Not React: this audience wants to open DevTools and understand what's happening; small bundle matters on a Pi.
- `docker-compose up` deployment, config via `.env`

**v1.1:**
- Cloud S3 backend support (second implementation of the same `storage/base.py` interface — proves the abstraction actually holds)

**v1.2:**
- USB/external drive auto-detect as Garage storage source (Linux host only)
- Explicit-confirm XFS formatting flow
- This was pulled out of core v1 deliberately: it needs host-level udev access, likely a privileged sidecar/helper container, and careful partition-table parsing — a distinct sub-project, not a checkbox alongside compression and UI work.

**Explicitly out of v1/v1.1/v1.2 (backlog for v2+):**
- Hosted/SaaS tier, multi-tenancy, billing
- Client-side zero-knowledge encryption
- Sync-watch-folder mode
- Multi-backend mirroring / hot-cold tiering
- Dedup
- AI agent helper (cleanup/archive/directory-structure suggestions, confirm-before-act)
- Shareable links with expiry
- API keys / access tokens for external scripts (beyond the basic v1 auth)

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

## 9. Open Questions

- Finalize MVP in/out list (Section 6) — draft only so far.
- Repo/package name and branding.
- Compression: which formats/strategies ship in v1 vs. later (see brainstorm backlog).
- Docs structure for launch (README, ARCHITECTURE.md, CONTRIBUTING.md).