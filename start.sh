#!/usr/bin/env bash
#
# claude-code-stack-zh 一键启动脚本
# 同时启动 team-memory-server 和 code-context-server
#

set -e

# ── 颜色定义 ──────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ── 项目根目录（基于脚本所在位置）──────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TEAM_MEMORY_DIR="${SCRIPT_DIR}/packages/team-memory-server/src/team_memory_server"
CODE_CONTEXT_DIR="${SCRIPT_DIR}/packages/code-context-server/src/code_context_server"

# ── PID 文件路径 ──────────────────────────────────────
PID_DIR="${SCRIPT_DIR}/.pids"
mkdir -p "${PID_DIR}"

# ── 停止函数 ──────────────────────────────────────────
stop_services() {
    echo -e "\n${YELLOW}🛑 正在停止服务...${NC}"

    for pid_file in "${PID_DIR}"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid
            pid=$(cat "$pid_file")
            local name
            name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                echo -e "  ${RED}✗${NC} ${name} (PID: ${pid}) 已停止"
            else
                echo -e "  ${YELLOW}⚠${NC} ${name} (PID: ${pid}) 已不存在"
            fi
            rm -f "$pid_file"
        fi
    done

    echo -e "${GREEN}所有服务已停止${NC}"
    exit 0
}

trap stop_services INT TERM

# ── 检查依赖 ──────────────────────────────────────────
echo -e "${CYAN}🔍 检查环境...${NC}"

if ! command -v uv &>/dev/null; then
    echo -e "${RED}❌ 未找到 uv，请先安装：https://docs.astral.sh/uv/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ uv 已安装${NC}"

# ── 安装依赖 ──────────────────────────────────────────
echo -e "${CYAN}📦 安装依赖...${NC}"
cd "${SCRIPT_DIR}"
uv sync --quiet
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# ── 启动 team-memory-server ──────────────────────────
echo -e "\n${CYAN}🚀 启动 team-memory-server...${NC}"
uv run --directory "${TEAM_MEMORY_DIR}" server.py &
TEAM_PID=$!
echo "$TEAM_PID" > "${PID_DIR}/team-memory-server.pid"
echo -e "  ${GREEN}✓${NC} team-memory-server 已启动  ${CYAN}PID: ${TEAM_PID}${NC}"

# ── 启动 code-context-server ─────────────────────────
echo -e "${CYAN}🚀 启动 code-context-server...${NC}"
uv run --directory "${CODE_CONTEXT_DIR}" server.py &
CODE_PID=$!
echo "$CODE_PID" > "${PID_DIR}/code-context-server.pid"
echo -e "  ${GREEN}✓${NC} code-context-server 已启动  ${CYAN}PID: ${CODE_PID}${NC}"

# ── 输出汇总 ──────────────────────────────────────────
echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 所有 MCP 服务已启动${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e ""
echo -e "  team-memory-server   PID: ${CYAN}${TEAM_PID}${NC}"
echo -e "  code-context-server  PID: ${CYAN}${CODE_PID}${NC}"
echo -e ""
echo -e "  ${YELLOW}停止服务：${NC}"
echo -e "    kill ${TEAM_PID} ${CODE_PID}"
echo -e "    或按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
echo -e ""

# ── 等待子进程 ────────────────────────────────────────
wait
