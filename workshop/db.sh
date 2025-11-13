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
HOST_PORT="${GEO_PG_PORT:-5432}"
COMMAND="${1:-start}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for database management." >&2
  exit 1
fi

container_running() {
  docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"
}

container_exists() {
  docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"
}

case "$COMMAND" in
  start)
    echo "[db] Building Postgres image (${IMAGE_NAME})"
    docker build -t "$IMAGE_NAME" . >/dev/null
    if container_running; then
      echo "[db] Container ${CONTAINER_NAME} already running"
      exit 0
    fi
    if container_exists; then
      echo "[db] Removing old container ${CONTAINER_NAME}"
      docker rm -f "$CONTAINER_NAME" >/dev/null
    fi
    echo "[db] Starting ${CONTAINER_NAME} on port ${HOST_PORT}"
    docker run -d --name "$CONTAINER_NAME" -e POSTGRES_PASSWORD=postgres -p "${HOST_PORT}:5432" "$IMAGE_NAME" >/dev/null
    ;;
  stop)
    if container_exists; then
      echo "[db] Stopping ${CONTAINER_NAME}"
      docker rm -f "$CONTAINER_NAME" >/dev/null
    else
      echo "[db] No container named ${CONTAINER_NAME} to stop"
    fi
    ;;
  status)
    if container_running; then
      echo "running"
      exit 0
    fi
    echo "stopped"
    exit 1
    ;;
  wait)
    if ! container_running; then
      echo "[db] Container ${CONTAINER_NAME} is not running" >&2
      exit 1
    fi
    echo "[db] Waiting for ${CONTAINER_NAME} to accept connections"
    until docker exec "$CONTAINER_NAME" pg_isready -U postgres >/dev/null 2>&1; do
      sleep 1
      echo -n '.'
    done
    echo
    ;;
  *)
    echo "Usage: db.sh {start|stop|status|wait}" >&2
    exit 1
    ;;
esac
