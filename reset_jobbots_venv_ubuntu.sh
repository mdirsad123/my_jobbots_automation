#!/usr/bin/env bash
set -Eeuo pipefail

# Run this script from the JobBots project root after replacing pyproject.toml.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED="${HOME}/ird-projects/my_jobbots_automation"
if [[ "$ROOT" != "$EXPECTED" || ! -f "$ROOT/linkedin/linkedin_fastapi.py" ]]; then
  echo "ERROR: Put this script in $EXPECTED and run it there." >&2
  exit 1
fi
cd "$ROOT"
if [[ ! -f pyproject.toml ]] || grep -Eq '^\s*(torch|transformers|sagemaker)\s*=' pyproject.toml; then
  echo "ERROR: Replace pyproject.toml with the supplied lightweight version first." >&2
  exit 1
fi
if ! command -v poetry >/dev/null 2>&1; then
  echo "ERROR: Poetry is not available in PATH." >&2
  exit 1
fi
if command -v uv >/dev/null 2>&1; then
  PY312="$(uv python find 3.12)"
elif command -v python3.12 >/dev/null 2>&1; then
  PY312="$(command -v python3.12)"
else
  echo "ERROR: Python 3.12 not found. Install it with: uv python install 3.12" >&2
  exit 1
fi

cat <<MESSAGE
Project: $ROOT
Python:  $PY312
Action:  Recreate ONLY $ROOT/.venv and regenerate poetry.lock.
Stop the LinkedIn API first. Recruiter Email uses a separate .venv and is untouched.
MESSAGE
read -r -p 'Type RESET to continue: ' RESPONSE
if [[ "$RESPONSE" != 'RESET' ]]; then
  echo 'Cancelled; no changes made.'
  exit 0
fi
BACKUPS="${HOME}/jobbot-install-backups"
mkdir -p "$BACKUPS"
STAMP="$(date +%Y%m%d-%H%M%S)"
cp pyproject.toml "$BACKUPS/pyproject-arm64-$STAMP.toml"
if [[ -f poetry.lock ]]; then
  mv poetry.lock "$BACKUPS/poetry-pre-arm64-$STAMP.lock"
fi
if [[ -L .venv ]]; then
  echo "ERROR: .venv is a symlink. Refusing to delete it." >&2
  exit 1
fi
if [[ -d .venv ]]; then
  rm -rf -- "$ROOT/.venv"
fi
unset VIRTUAL_ENV POETRY_ACTIVE || true
poetry config virtualenvs.in-project true --local
poetry env use "$PY312"
poetry lock
poetry install --only main --no-root
poetry run python -c 'import fastapi, starlette, uvicorn, selenium, requests, pandas; print("Core packages OK")'
echo
poetry env info --path
echo "Done. Start API with: cd linkedin/bat_file && ./start_linkedin_fastapi.sh"
echo "Optional GUI packages: poetry install --with desktop --no-root"
