#!/usr/bin/env bash
# ─── Render Build Script ──────────────────────────────────
# Runs during every deploy on Render
# ──────────────────────────────────────────────────────────
set -o errexit   # exit on error

echo "▸ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "▸ Running database migrations..."
python migrate.py

echo "▸ Seeding database (skips if data already exists)..."
python seed.py

echo "✓ Build complete."
