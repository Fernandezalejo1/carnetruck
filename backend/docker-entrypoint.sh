#!/bin/sh
set -e

echo "Aplicando migraciones..."
alembic upgrade head

echo "Arrancando API en 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
