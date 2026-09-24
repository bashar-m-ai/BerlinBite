#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f .env ]; then cp .env.example .env; chmod 600 .env; fi
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest backend/tests -q
printf '\nOpen http://127.0.0.1:8000 in your browser. Press Control-C to stop.\n'
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
