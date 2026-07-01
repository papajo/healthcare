#!/usr/bin/env bash
# Crisis-Cost Orchestrator — Stop Script
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT/.pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

stop_service() {
  local name=$1
  local screen_name=$2
  local pidfile="$PID_DIR/$name.pid"

  # Try stopping by PID file first
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
      echo -e "  ${GREEN}✓ $name stopped (pid $pid)${NC}"
    else
      echo -e "  ${YELLOW}○ $name — already stopped${NC}"
    fi
    rm -f "$pidfile"
  fi

  # Try stopping screen session
  if command -v screen &>/dev/null; then
    if screen -list 2>/dev/null | grep -q "$screen_name"; then
      screen -S "$screen_name" -X quit 2>/dev/null || true
      echo -e "  ${GREEN}✓ $name screen session killed${NC}"
    fi
  fi
}

# ─── Parse args ──────────────────────────────────────────────────────────────

DOCKER_ONLY=false
API_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case $arg in
    --docker-only) DOCKER_ONLY=true ;;
    --api-only) API_ONLY=true ;;
    --frontend-only) FRONTEND_ONLY=true ;;
    --help|-h)
      echo "Usage: ./stop.sh [--docker-only|--api-only|--frontend-only]"
      exit 0
      ;;
  esac
done

# ─── Stop processes ──────────────────────────────────────────────────────────

if [ "$DOCKER_ONLY" = false ]; then
  echo -e "\n${CYAN}━━━ Stopping Services ━━━${NC}"

  if [ "$FRONTEND_ONLY" = false ]; then
    stop_service api coco-api
  fi
  if [ "$API_ONLY" = false ]; then
    stop_service frontend coco-frontend
  fi
fi

# ─── Stop Docker ─────────────────────────────────────────────────────────────

if [ "$API_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
  echo -e "\n${CYAN}━━━ Docker Services ━━━${NC}"

  if ! command -v docker &>/dev/null || ! docker info >/dev/null 2>&1; then
    echo -e "  ${YELLOW}○ Docker not available — skipping${NC}"
  elif docker compose ps --status running 2>/dev/null | grep -q .; then
    docker compose -f "$ROOT/docker-compose.yml" down 2>/dev/null
    echo -e "  ${GREEN}✓ Docker services stopped${NC}"
  else
    echo -e "  ${YELLOW}○ Docker services already stopped${NC}"
  fi
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo -e "\n${GREEN}━━━ All Services Stopped ━━━${NC}"
echo ""
