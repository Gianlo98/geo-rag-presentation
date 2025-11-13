#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DB_SCRIPT="$ROOT_DIR/db.sh"
DB_STARTED_BY_SCRIPT=0
if "$DB_SCRIPT" status >/dev/null 2>&1; then
  echo "[db] Reusing running Postgres container"
else
  "$DB_SCRIPT" start
  DB_STARTED_BY_SCRIPT=1
fi

cleanup() {
  if [ "$DB_STARTED_BY_SCRIPT" -eq 1 ]; then
    "$DB_SCRIPT" stop
  fi
}
trap cleanup EXIT

"$DB_SCRIPT" wait

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

streamlit run debug.py --server.port "${GEO_DEBUG_PORT:-8501}"
