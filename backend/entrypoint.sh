#!/bin/sh
# Entrypoint api-контейнера: ждём db, накатываем миграции, сеем демо-данные, стартуем сервер.
# Все вызовы — явными путями из /app/.venv (venv не активирован в exec-сессиях).
set -e

cd /app

echo "waiting for db..."
i=0
while ! /app/.venv/bin/python -c "import socket; socket.create_connection(('db', 5432), timeout=2)" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "db not reachable after 60s, giving up" >&2
    exit 1
  fi
  sleep 1
done
echo "db is up"

/app/.venv/bin/alembic upgrade head
/app/.venv/bin/python scripts/seed.py

exec "$@"
