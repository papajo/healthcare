#!/usr/bin/env bash
# Crisis-Cost Orchestrator — Start Script
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS="$ROOT/.logs"
PID_DIR="$ROOT/.pids"

mkdir -p "$LOGS" "$PID_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

is_running() {
  local pidfile="$PID_DIR/$1.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    rm -f "$pidfile"
  fi
  return 1
}

wait_for_port() {
  local port=$1
  local name=$2
  local max=30
  local i=0
  while ! nc -z localhost "$port" 2>/dev/null; do
    i=$((i + 1))
    if [ "$i" -ge "$max" ]; then
      echo -e "  ${RED}✗ $name failed to start on port $port${NC}"
      return 1
    fi
    sleep 1
  done
  echo -e "  ${GREEN}✓ $name ready on port $port${NC}"
}

# ─── Parse args ──────────────────────────────────────────────────────────────

COMPOSE_ONLY=false
API_ONLY=false
FRONTEND_ONLY=false
FOREGROUND=false

for arg in "$@"; do
  case $arg in
    --docker-only) COMPOSE_ONLY=true ;;
    --api-only) API_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
    --fg|--foreground) FOREGROUND=true ;;
    --help|-h)
      echo "Usage: ./start.sh [options]"
      echo ""
      echo "  (no args)       Start everything in background (requires screen)"
      echo "  --fg/--foreground Start in foreground (Ctrl+C to stop)"
      echo "  --docker-only   Start only Postgres, Redis, Temporal"
      echo "  --api-only      Start only the FastAPI backend"
      echo "  --frontend-only Start only the React dev server"
      exit 0
      ;;
  esac
done

# ─── Docker services ─────────────────────────────────────────────────────────

if [ "$API_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
  echo -e "\n${CYAN}━━━ Docker Services ━━━${NC}"

  if ! command -v docker &>/dev/null; then
    echo -e "  ${YELLOW}⚠ Docker not found — skipping infrastructure${NC}"
  elif ! docker info >/dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠ Docker daemon not running — skipping infrastructure${NC}"
    echo -e "  ${YELLOW}  Start Colima first: colima start${NC}"
  elif docker compose ps --status running 2>/dev/null | grep -q postgres; then
    echo -e "  ${GREEN}✓ Docker services already running${NC}"
  else
    echo "  Starting Postgres, Redis, Temporal..."
    if docker compose -f "$ROOT/docker-compose.yml" up -d 2>"$LOGS/docker.log"; then
      echo -e "  ${GREEN}✓ Docker services started${NC}"
    else
      echo -e "  ${YELLOW}⚠ Docker compose failed — check $LOGS/docker.log${NC}"
      echo -e "  ${YELLOW}  Continuing without infrastructure (API will run in-memory mode)${NC}"
    fi
  fi
fi

# ─── Foreground mode ─────────────────────────────────────────────────────────

if [ "$FOREGROUND" = true ]; then
  echo -e "\n${CYAN}━━━ Starting in foreground (Ctrl+C to stop) ━━━${NC}"
  echo ""

  if [ "$COMPOSE_ONLY" = true ]; then
    echo "Docker services running. Press Ctrl+C to stop."
    wait
    exit 0
  fi

  # Build command list
  CMDS=()
  if [ "$FRONTEND_ONLY" = false ]; then
    CMDS+=("uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload")
  fi
  if [ "$API_ONLY" = false ]; then
    CMDS+=("(cd frontend && npm run dev)")
  fi

  # Run with trap for cleanup
  trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; kill 0; exit 0' INT TERM

  for cmd in "${CMDS[@]}"; do
    eval "$cmd" &
  done

  wait
  exit 0
fi

# ─── Background mode (uses screen) ──────────────────────────────────────────

if ! command -v screen &>/dev/null; then
  echo -e "\n${RED}screen not found. Install it:${NC}"
  echo "  brew install screen"
  echo ""
  echo "Or run in foreground: ./start.sh --fg"
  exit 1
fi

# ─── API Server ──────────────────────────────────────────────────────────────

if [ "$COMPOSE_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
  echo -e "\n${CYAN}━━━ API Server (FastAPI) ━━━${NC}"

  if is_running api; then
    echo -e "  ${GREEN}✓ API already running (pid $(cat "$PID_DIR/api.pid"))${NC}"
  else
    if screen -list 2>/dev/null | grep -q coco-api; then
      echo -e "  ${YELLOW}⚠ screen session 'coco-api' already exists${NC}"
    else
      screen -dmS coco-api bash -c "cd $ROOT && uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload >> $LOGS/api.log 2>&1"
      sleep 2
      # Capture the screen PID
      screen -pid coco-api > "$PID_DIR/api.pid" 2>/dev/null || echo "screen-managed" > "$PID_DIR/api.pid"
    fi
    wait_for_port 8000 "API Server"
  fi
fi

# ─── Frontend ────────────────────────────────────────────────────────────────

if [ "$COMPOSE_ONLY" = false ] && [ "$API_ONLY" = false ]; then
  echo -e "\n${CYAN}━━━ Frontend (React + Vite) ━━━${NC}"

  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    echo "  Installing frontend dependencies..."
    (cd "$ROOT/frontend" && npm install --silent) > "$LOGS/frontend-install.log" 2>&1
  fi

  if is_running frontend; then
    echo -e "  ${GREEN}✓ Frontend already running (pid $(cat "$PID_DIR/frontend.pid"))${NC}"
  else
    if screen -list 2>/dev/null | grep -q coco-frontend; then
      echo -e "  ${YELLOW}⚠ screen session 'coco-frontend' already exists${NC}"
    else
      screen -dmS coco-frontend bash -c "cd $ROOT/frontend && npm run dev >> $LOGS/frontend.log 2>&1"
      sleep 2
      screen -pid coco-frontend > "$PID_DIR/frontend.pid" 2>/dev/null || echo "screen-managed" > "$PID_DIR/frontend.pid"
    fi
    wait_for_port 5173 "Frontend"
  fi
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo -e "\n${GREEN}━━━ All Services Started ━━━${NC}"
echo ""
echo "  API:       http://localhost:8000"
echo "  Swagger:   http://localhost:8000/docs"
echo "  Frontend:  http://localhost:5173"
echo ""
echo "  Logs:      $LOGS/"
echo "  Status:    ./status.sh"
echo "  Stop all:  ./stop.sh"
echo ""
