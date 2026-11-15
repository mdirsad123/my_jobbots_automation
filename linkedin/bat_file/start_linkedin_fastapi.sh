#!/usr/bin/env bash
# Ubuntu (Oracle ARM64) equivalent of start_linkedin_fastapi.bat.
# Put this file at ~/ird-projects/my_jobbots_automation/linkedin/bat_file/start_linkedin_fastapi.sh
# Starts/reuses the shared Chromium DevTools session (9222) and runs LinkedIn FastAPI (8010 by default).
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Script lives in PROJECT_ROOT/linkedin/bat_file; go up two directories.
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
CHROME_PORT="9222"
API_HOST="127.0.0.1"
API_PORT="${LINKEDIN_API_PORT:-8010}"
CHROME_HELPER="$HOME/ird-projects/auto-email-recruiter-reply/start_chromium_debug.sh"

info() { printf '[JobBots] %s\n' "$*"; }
fail() { printf '[JobBots] ERROR: %s\n' "$*" >&2; exit 1; }

devtools_ready() {
  # Check the actual DevTools endpoint, not only whether port 9222 is open.
  curl --noproxy '*' --silent --show-error --fail --max-time 2 \
    "http://127.0.0.1:${CHROME_PORT}/json/version" 2>/dev/null \
    | grep -q 'webSocketDebuggerUrl'
}

printf '\n========== JobBots LinkedIn FastAPI (Ubuntu) ==========\n'

info '[1/4] Checking project ...'
[[ -f "$PROJECT_ROOT/linkedin/linkedin_fastapi.py" ]] || \
  fail "Missing: $PROJECT_ROOT/linkedin/linkedin_fastapi.py"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
info "Project: $PROJECT_ROOT"

info "[2/4] Checking shared Chromium debugger on 127.0.0.1:${CHROME_PORT} ..."
command -v curl >/dev/null 2>&1 || fail 'curl missing; install: sudo apt install -y curl'
if devtools_ready; then
  info 'Shared Chromium debugger already running. Reusing it.'
else
  if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    fail "Chromium debugger is off. Open a terminal INSIDE RustDesk/XFCE, run: bash '$CHROME_HELPER' ; then rerun this script (SSH terminal works once browser is running)."
  fi
  [[ -f "$CHROME_HELPER" ]] || \
    fail "Chromium startup helper missing: $CHROME_HELPER. Start Chromium with debugger port 9222 from the Ubuntu desktop."
  info 'Starting shared Chromium in the Ubuntu desktop ...'
  CHROME_DEBUG_PORT="$CHROME_PORT" bash "$CHROME_HELPER" || fail 'Chromium debugger startup failed.'
  for i in {1..15}; do
    devtools_ready && break
    sleep 2
  done
  devtools_ready || fail 'Chromium debugger is not ready on port 9222.'
  info 'Chromium debugger ready.'
fi

info '[3/4] Checking existing project .venv ...'
[[ -x "$VENV_PYTHON" ]] || \
  fail "Missing $VENV_PYTHON. First run Poetry installation in my_jobbots_automation."
"$VENV_PYTHON" -c 'import fastapi, uvicorn' >/dev/null 2>&1 || \
  fail "FastAPI/Uvicorn missing in project .venv. Run: cd '$PROJECT_ROOT' && poetry add fastapi uvicorn (or install via your existing Poetry dependency setup)."
info "Python: $("$VENV_PYTHON" --version 2>&1)"
info 'Existing Poetry .venv ready.'

# Check port before starting so we do not collide with AlgoAgentX (8000).
"$VENV_PYTHON" - "$API_HOST" "$API_PORT" <<'PY_CHECK_PORT'
import socket
import sys
host, port_raw = sys.argv[1:]
try:
    port = int(port_raw)
    if not 1 <= port <= 65535:
        raise ValueError
except ValueError:
    print(f"[JobBots] ERROR: Invalid port: {port_raw}", file=sys.stderr)
    sys.exit(1)
with socket.socket() as sock:
    sock.settimeout(1)
    if sock.connect_ex((host, port)) == 0:
        print(f"[JobBots] ERROR: Port {port} already in use. Choose another LINKEDIN_API_PORT.", file=sys.stderr)
        sys.exit(1)
PY_CHECK_PORT

info "[4/4] Starting LinkedIn FastAPI on ${API_HOST}:${API_PORT} ..."
info "API docs: http://${API_HOST}:${API_PORT}/docs"
info 'Press Ctrl+C to stop the API. Chromium will remain open.'
exec "$VENV_PYTHON" -m uvicorn linkedin.linkedin_fastapi:app \
  --host "$API_HOST" --port "$API_PORT"
