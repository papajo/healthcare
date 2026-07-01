#!/usr/bin/env bash
# Crisis-Cost Orchestrator — Status Script
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT/.pids"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check_port() {
  nc -z localhost "$1" 2>/dev/null
}

check_screen() {
  command -v screen &>/dev/null && screen -list 2>/dev/null | grep -q "$1"
}

check_service() {
  local name=$1
  local screen_name=$2
  local port=$3
  local pidfile="$PID_DIR/$name.pid"

  local running=false
  local method=""

  # Check PID file
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      running=true
      method="pid=$pid"
    fi
  fi

  # Check screen session
  if [ "$running" = false ] && check_screen "$screen_name"; then
    running=true
    method="screen=$screen_name"
  fi

  # Check port
  if [ "$running" = false ] && check_port "$port"; then
    running=true
    method="port=$port (not managed)"
  fi

  if [ "$running" = true ]; then
    echo -e "  ${GREEN}● $name${NC}  $method"
  else
    echo -e "  ${RED}○ $name${NC}  port=$port  not running"
  fi
}

echo -e "\n${CYAN}━━━ Crisis-Cost Orchestrator ━━━${NC}\n"

check_service "API Server" "coco-api" 8000
check_service "Frontend" "coco-frontend" 5173
check_port 5432 && \
  echo -e "  ${GREEN}● PostgreSQL  ${NC}  port=5432" || \
  echo -e "  ${RED}○ PostgreSQL  ${NC}  port=5432  not running"
check_port 6379 && \
  echo -e "  ${GREEN}● Redis       ${NC}  port=6379" || \
  echo -e "  ${RED}○ Redis       ${NC}  port=6379  not running"
check_port 7233 && \
  echo -e "  ${GREEN}● Temporal    ${NC}  port=7233" || \
  echo -e "  ${RED}○ Temporal    ${NC}  port=7233  not running"

# Health endpoint
if check_port 8000; then
  HEALTH=$(curl -sf http://localhost:8000/health 2>/dev/null || echo '{"status":"unreachable"}')
  READY=$(curl -sf http://localhost:8000/ready 2>/dev/null || echo '{"status":"unreachable"}')
  echo ""
  echo -e "  ${CYAN}Health:${NC}  $HEALTH"
  echo -e "  ${CYAN}Ready:${NC}   $READY"
fi

echo ""
