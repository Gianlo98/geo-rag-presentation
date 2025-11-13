#!/usr/bin/env bash
set -euo pipefail

REQUIRED_PY_SHORT="3.10"
REQUIRED_PY_FULL="3.10.14"
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
RUNTIME_DIR="$SCRIPT_DIR/.python-runtime"
PYTHON_BIN=""
VENV_STATUS="missing"

finish() {
  local code=${1:-0}
  if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return "$code"
  fi
  exit "$code"
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_python_available() {
  if command_exists "python${REQUIRED_PY_SHORT}"; then
    PYTHON_BIN="$(command -v python${REQUIRED_PY_SHORT})"
    return
  fi

  if command_exists pyenv; then
    PYENV_PREFIX="$(pyenv root)/versions/${REQUIRED_PY_FULL}"
    if [ ! -x "$PYENV_PREFIX/bin/python${REQUIRED_PY_SHORT}" ]; then
      echo "[setup] Installing Python ${REQUIRED_PY_FULL} via pyenv..."
      pyenv install -s "${REQUIRED_PY_FULL}"
    fi
    PYTHON_BIN="$PYENV_PREFIX/bin/python${REQUIRED_PY_SHORT}"
    return
  fi

  download_python_source
}

download_python_source() {
  mkdir -p "$RUNTIME_DIR/src"
  local install_prefix="$RUNTIME_DIR/$REQUIRED_PY_FULL"
  local python_path="$install_prefix/bin/python${REQUIRED_PY_SHORT}"
  if [ -x "$python_path" ]; then
    PYTHON_BIN="$python_path"
    return
  fi

  local tarball="Python-${REQUIRED_PY_FULL}.tgz"
  local url="https://www.python.org/ftp/python/${REQUIRED_PY_FULL}/${tarball}"
  local tar_dest="$RUNTIME_DIR/${tarball}"

  echo "[setup] Downloading Python ${REQUIRED_PY_FULL} from ${url}..."
  if command_exists curl; then
    curl -L "$url" -o "$tar_dest"
  elif command_exists wget; then
    wget -O "$tar_dest" "$url"
  else
    echo "[setup] Error: need curl or wget to download Python ${REQUIRED_PY_FULL}." >&2
    finish 1
  fi

  echo "[setup] Extracting ${tarball}..."
  tar -xzf "$tar_dest" -C "$RUNTIME_DIR/src"
  local build_dir="$RUNTIME_DIR/src/Python-${REQUIRED_PY_FULL}"

  echo "[setup] Compiling Python ${REQUIRED_PY_FULL} (this may take a while)..."
  pushd "$build_dir" >/dev/null
  ./configure --prefix="$install_prefix"
  local cpu_count
  cpu_count=$( (command_exists sysctl && sysctl -n hw.ncpu) || (command_exists nproc && nproc) || echo 4 )
  make -j"$cpu_count"
  make install
  popd >/dev/null

  PYTHON_BIN="$python_path"
}

ensure_correct_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    VENV_STATUS="missing"
    return
  fi
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    rm -rf "$VENV_DIR"
    VENV_STATUS="missing"
    return
  fi
  local current_version
  current_version="$($VENV_DIR/bin/python -c 'import platform; print(platform.python_version())')"
  if [[ "$current_version" != ${REQUIRED_PY_SHORT}.* ]]; then
    echo "[setup] Existing .venv uses Python ${current_version}; rebuilding with ${REQUIRED_PY_FULL}."
    rm -rf "$VENV_DIR"
    VENV_STATUS="missing"
  else
    VENV_STATUS="ready"
    export VIRTUAL_ENV="$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "[setup] Activated existing virtualenv (Python ${current_version})."
  fi
}

create_venv() {
  echo "[setup] Creating virtualenv with ${PYTHON_BIN}..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip
  pip install -r "$SCRIPT_DIR/requirements.txt"
}

ensure_correct_venv
if [ "$VENV_STATUS" = "ready" ]; then
  echo "[setup] Environment ready in ${VENV_DIR}."
  finish 0
fi

ensure_python_available
if [ -z "$PYTHON_BIN" ]; then
  echo "[setup] Error: unable to locate or build Python ${REQUIRED_PY_FULL}." >&2
  finish 1
fi
create_venv

echo "[setup] Environment created and activated in ${VENV_DIR}."
finish 0
