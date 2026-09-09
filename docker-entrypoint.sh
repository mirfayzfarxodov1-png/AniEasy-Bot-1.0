#!/bin/sh
set -eu

echo "[AniEasy] Running database migrations..."
alembic upgrade head

echo "[AniEasy] Starting AniEasy Bot 1.0..."
exec python -m app.main
