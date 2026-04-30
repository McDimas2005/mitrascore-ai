#!/bin/sh
set -eu

cd "$(dirname "$0")"
APP_ROOT="$(pwd)"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"
export PYTHONPATH="${APP_ROOT}/.python_packages/lib/site-packages:/home/site/wwwroot/.python_packages/lib/site-packages:${PYTHONPATH:-}"

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

echo "Starting MitraScore API from ${APP_ROOT}"
echo "Python: $(command -v "$PYTHON_BIN")"
"$PYTHON_BIN" --version
echo "Django settings module: ${DJANGO_SETTINGS_MODULE}"
"$PYTHON_BIN" - <<'PY'
import importlib.util
import os
import sys

for package in ("django", "gunicorn", "psycopg2", "rest_framework"):
    spec = importlib.util.find_spec(package)
    print(f"{package}: {'found at ' + spec.origin if spec else 'NOT FOUND'}")

print(f"WEBSITE_HOSTNAME={os.environ.get('WEBSITE_HOSTNAME', '')}")
print(f"WEBSITES_PORT={os.environ.get('WEBSITES_PORT', '')}")
print(f"PORT={os.environ.get('PORT', '')}")
print(f"sys.path[0:5]={sys.path[0:5]}")
PY

exec "$PYTHON_BIN" -m gunicorn config.wsgi:application \
  --bind "0.0.0.0:${WEBSITES_PORT:-${PORT:-8000}}" \
  --timeout "${GUNICORN_TIMEOUT:-600}" \
  --access-logfile "-" \
  --error-logfile "-" \
  --capture-output
