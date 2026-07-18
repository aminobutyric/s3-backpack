#!/usr/bin/env bash
# One-time setup: generates garage/garage.toml with real secrets from the
# checked-in template. garage/garage.toml is gitignored — never commit it.
set -euo pipefail

TEMPLATE="garage/garage.toml.example"
OUTPUT="garage/garage.toml"

if [ -f "$OUTPUT" ]; then
  echo "garage/garage.toml already exists — refusing to overwrite. Delete it first if you want to regenerate secrets." >&2
  exit 1
fi

RPC_SECRET=$(openssl rand -hex 32)
ADMIN_TOKEN=$(openssl rand -base64 32)
METRICS_TOKEN=$(openssl rand -base64 32)

sed \
  -e "s|__RPC_SECRET__|${RPC_SECRET}|" \
  -e "s|__ADMIN_TOKEN__|${ADMIN_TOKEN}|" \
  -e "s|__METRICS_TOKEN__|${METRICS_TOKEN}|" \
  "$TEMPLATE" > "$OUTPUT"

echo "Wrote $OUTPUT"
echo
echo "Next: copy .env.example to .env, then set GARAGE_DEFAULT_ACCESS_KEY / GARAGE_DEFAULT_SECRET_KEY"
echo "  GARAGE_DEFAULT_ACCESS_KEY: GK\$(openssl rand -hex 16)"
echo "  GARAGE_DEFAULT_SECRET_KEY: \$(openssl rand -hex 32)"