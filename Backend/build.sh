#!/usr/bin/env bash
# ─── Render Build Script ──────────────────────────────────
# Runs during every deploy on Render
# ──────────────────────────────────────────────────────────
set -o errexit   # exit on error

echo "▸ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

RUN_DB_SETUP_ON_BUILD="${RUN_DB_SETUP_ON_BUILD:-0}"
if [ "$RUN_DB_SETUP_ON_BUILD" = "1" ]; then
  echo "▸ Running database migrations..."
  if ! python migrate.py; then
    echo "⚠ Migrations failed during build; continuing deploy (startup migration will retry)."
  fi

  echo "▸ Seeding database (skips if data already exists)..."
  if ! python seed.py; then
    echo "⚠ Seed failed during build; continuing deploy."
  fi
else
  echo "▸ Skipping build-time migration/seed (RUN_DB_SETUP_ON_BUILD=0)."
fi

echo "✓ Build complete."
