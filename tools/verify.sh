#!/bin/sh
# Offline verification gate. No hardware required.
# Usage: ./tools/verify.sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "Missing $PY. Create it first (python3 -m venv .venv)." >&2
    exit 1
fi

echo "==> tests (7 offline checks, live Open-Meteo fetch, retry once on flake)"
if ! "$PY" tests/test_app.py; then
    echo "First run failed, retrying once (Open-Meteo fetch is live)..." >&2
    "$PY" tests/test_app.py
fi

echo "==> py_compile"
"$PY" -m py_compile app/main.py app/fonts.py tests/test_app.py

echo "VERIFY OK"
