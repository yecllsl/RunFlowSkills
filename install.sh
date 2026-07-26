#!/usr/bin/env bash
# RunFlowSkills 安装脚本
# 适用于 Linux / macOS
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

set -e

echo ""
echo "========================================"
echo "  RunFlowSkills v0.1.0 安装向导"
echo "========================================"
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
echo "[1/5] 检查 uv 包管理器..."
if ! command -v uv &> /dev/null; then
    echo "  ✗ uv 未安装"
    echo ""
    echo "  请先安装 uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  或访问 https://docs.astral.sh/uv/getting-started/install/"
    exit 1
fi
echo "  ✓ uv 已安装 ($(uv --version))"

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
echo "[2/5] 检查 Python 版本 (>=3.12)..."
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 未安装"
    echo ""
    echo "  请先安装 Python 3.12+："
    echo "  https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo "  ✗ Python 版本过低: $PYTHON_VERSION (需要 >= 3.12)"
    echo ""
    echo "  请升级 Python: https://www.python.org/downloads/"
    exit 1
fi
echo "  ✓ Python $PYTHON_VERSION"

# ──────────────────────────────────────────
# [3/5] 安装依赖
# ──────────────────────────────────────────
echo "[3/5] 安装依赖..."

cd "$PROJECT_ROOT/run-flow-skills-mcp"

echo "  正在安装依赖包..."
if ! uv sync 2>&1; then
    echo "  ✗ 依赖安装失败"
    echo ""
    echo "  请尝试手动安装："
    echo "  cd run-flow-skills-mcp"
    echo "  uv sync"
    exit 1
fi
echo "  ✓ 依赖安装完成"

# ──────────────────────────────────────────
# [4/5] 下载 Web 静态资源（可选）
# ──────────────────────────────────────────
echo "[4/5] 下载 Web 静态资源（可选）..."
echo "  Web 可视化需要 HTMX/Alpine.js/ECharts（约 1MB）"
read -p "  下载静态资源？[Y/n] " download_static
if [[ "$download_static" =~ ^[Yy]$|^$ ]]; then
    script_path="src/run_flow_skills_mcp/web/static/download_static.sh"
    if [ -f "$script_path" ]; then
        bash "$script_path"
    else
        echo "  ⊘ 下载脚本不存在，可稍后手动运行：bash $script_path"
    fi
else
    echo "  ⊘ 已跳过。后续需要时运行：bash src/run_flow_skills_mcp/web/static/download_static.sh"
fi

# ──────────────────────────────────────────
# [5/5] 验证安装
# ──────────────────────────────────────────
echo "[5/5] 验证安装..."

# 验证 MCP Server 入口点可用
uv run run-flow-skills-mcp --help >/dev/null 2>&1 && echo "  ✓ MCP Server 入口点可用" || echo "  ⚠ MCP Server 验证跳过"

# 验证 Web 入口点可用
web_test=$(uv run python -c "from run_flow_skills_mcp.web.app import create_app; print('OK')" 2>&1)
if echo "$web_test" | grep -q "OK"; then
    echo "  ✓ Web 可视化模块可用"
else
    echo "  ⚠ Web 可视化模块验证跳过"
fi

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
echo ""
echo "========================================"
echo "  ✓ 安装完成！"
echo "========================================"
echo ""
echo "下一步操作（任选一个平台）："
echo ""
echo "  Trae IDE CN："
echo "    1. 文件 → 打开文件夹 → 选择: $PROJECT_ROOT"
echo "    2. 设置 → MCP → 打开'启用项目级 MCP'开关"
echo "    3. 重启 Trae"
echo ""
echo "  Claude Code："
echo "    claude /open $PROJECT_ROOT"
echo ""
echo "  Cursor / Windsurf / Continue："
echo "    打开文件夹即可（配置已入库）"
echo ""
echo "  OpenCode："
echo "    cd $PROJECT_ROOT && opencode"
echo ""
echo "  WorkBuddy："
echo "    打开文件夹即可（.workbuddy/mcp.json 已入库）"
echo ""
echo "开始使用："
echo "  /import  - 导入训练文件"
echo "  /analyze - 分析训练数据"
echo "  /plan    - 生成训练计划"
echo "  /review  - 复盘训练"
echo "  /coach   - AI 教练建议"
echo "  /stats   - 统计与导出"
echo ""
echo "可选：启动 Web 可视化界面"
echo "  cd run-flow-skills-mcp && uv run run-flow-skills-web"
echo "  浏览器访问 http://127.0.0.1:8002"
echo ""
echo "详细部署指南：见 DEPLOY.md 和 PLATFORMS.md"
echo ""
