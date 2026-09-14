#!/usr/bin/env bash
# Start / stop / restart the ETA service in the background, with a pidfile.
#   scripts/serve.sh start|stop|restart|status|logs
set -euo pipefail
cd "$(dirname "$0")/.."
PID=.run/service.pid
LOG=.run/service.log
PORT="${PORT:-8000}"
mkdir -p .run

start() {
  if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then
    echo "already running (pid $(cat "$PID"))"; return
  fi
  # Detach so the server outlives this shell. setsid is GNU-only — macOS
  # doesn't ship it — so use it when it's there and fall back to nohup alone.
  local cmd=(.venv/bin/python -m uvicorn eta.service:app --port "$PORT")
  command -v setsid >/dev/null 2>&1 && cmd=(setsid "${cmd[@]}")
  nohup "${cmd[@]}" >"$LOG" 2>&1 < /dev/null &
  echo $! > "$PID"
  # 60 s, not 20: with the optional `ui` extra installed the service also
  # imports gradio and builds the Blocks before it answers /health.
  for _ in $(seq 1 120); do
    sleep 0.5
    if curl -sf "localhost:$PORT/health" >/dev/null 2>&1; then
      echo "up on :$PORT (pid $(cat "$PID"))"; return
    fi
  done
  echo "did not come up in 60 s — see $LOG"; tail -20 "$LOG"; exit 1
}

stop() {
  if [ -f "$PID" ]; then
    local p
    p=$(cat "$PID")
    kill "$p" 2>/dev/null || true
    # uvicorn takes a couple of seconds to release the port. Returning before
    # it has makes `restart` race against itself, so actually wait.
    local i
    for i in $(seq 1 20); do
      kill -0 "$p" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$p" 2>/dev/null; then
      kill -9 "$p" 2>/dev/null || true
      sleep 1
      echo "stopped (had to SIGKILL $p)"
    else
      echo "stopped"
    fi
    rm -f "$PID"
    return
  fi
  # No pidfile but something may still own the port (a manually started
  # uvicorn, or a pidfile deleted by hand). lsof is on macOS and most Linuxes.
  if command -v lsof >/dev/null 2>&1; then
    local owner
    owner=$(lsof -ti :"$PORT" 2>/dev/null || true)
    if [ -n "$owner" ]; then
      echo "no pidfile, but pid $owner owns :$PORT — kill it with:  kill $owner"
      return
    fi
  fi
  echo "not running"
}

case "${1:-start}" in
  start)   start ;;
  stop)    stop ;;
  restart) stop; sleep 1; start ;;
  status)  curl -s "localhost:$PORT/health"; echo ;;
  logs)    tail -n "${2:-30}" "$LOG" ;;
  *)       echo "usage: $0 start|stop|restart|status|logs"; exit 1 ;;
esac
