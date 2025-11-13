#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

IMAGE_NAME="${GEO_PG_IMAGE:-geo-pgvector}"
CONTAINER_NAME="${GEO_PG_CONTAINER:-geo-pgvector}"
HOST_PORT="${GEO_PG_PORT:-5433}"
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:${HOST_PORT}/geo_rag}"
export DATABASE_URL

DB_SCRIPT="$PROJECT_ROOT/db.sh"
DB_STARTED_BY_SCRIPT=0
if "$DB_SCRIPT" status >/dev/null 2>&1; then
  echo "[db] Reusing running container ${CONTAINER_NAME}"
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
  echo "Creating Python virtual environment"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is required for embeddings and reranking. Set it in .env." >&2
  exit 1
fi

echo "[3/5] Ensuring embedding cache is up to date"
python scripts/build_embedding_cache.py

echo "[4/5] Running evaluation via run.py"
python run.py
