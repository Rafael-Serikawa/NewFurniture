#!/usr/bin/env bash
# Sobe o backend (porta 8000) e o frontend (porta 5173). Ctrl+C encerra os dois.
cd "$(dirname "$0")"
(cd backend && source .venv/bin/activate && python manage.py runserver) &
BACK=$!
trap "kill $BACK 2>/dev/null" EXIT
cd frontend && npm run dev
