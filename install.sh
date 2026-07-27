#!/usr/bin/env bash
# RunFlowSkills 安装脚本
# 适用于 Linux / macOS
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
#
# 特性：
#   - 自动使用项目内 uv（无需预装）
#   - 自动下载 Python 3.12+（如未安装）
#   - 使用国内镜像加速依赖安装

set -e

echo ""
echo "========================================"
echo "  RunFlowSkills v0.1.1 安装向导"
echo "========================================"
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ──────────────────────────────────────────
# 辅助函数：获取 uv 命令路径
# ──────────────────────────────────────────
get_uv_command() {
    # 优先使用系统 uv
    if command -v uv &> /dev/null; then
        echo "uv"
        return 0
    fi
    
    # 回退到项目内 uv
    local os_type="$(uname -s)"
    local machine_type="$(uname -m)"
    
    # 确定文件名
    local uv_binary="uv"
    if [[ "$os_type" == *"MINGW"* ]] || [[ "$os_type" == *"MSYS"* ]] || [[ "$os_type" == *"CYGWIN"* ]]; then
        uv_binary="uv.exe"
    fi
    
    local local_uv="$PROJECT_ROOT/tools/$uv_binary"
    if [[ -f "$local_uv" ]]; then
        echo "$local_uv"
        return 0
    fi
    
    # 都没有，返回空
    return 1
}

# ──────────────────────────────────────────
# 辅助函数：配置国内镜像源
# ──────────────────────────────────────────
set_chinese_mirror() {
    echo "  配置国内镜像源..."
    
    local uv_toml="$PROJECT_ROOT/run-flow-skills-mcp/uv.toml"
    
    if [[ ! -f "$uv_toml" ]]; then
        cat > "$uv_toml" << 'EOF'
# uv 国内镜像源配置
[[index]]
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true

[pip]
index-url = "https://mirrors.aliyun.com/pypi/simple/"
EOF
        echo "    ✓ 已创建 uv.toml 配置文件"
    else
        echo "    ⊘ uv.toml 已存在，跳过"
    fi
}

# ──────────────────────────────────────────
# [1/6] 检查并准备 uv
# ──────────────────────────────────────────
echo "[1/6] 检查 uv 包管理器..."

UV_COMMAND=""
if uv_cmd=$(get_uv_command); then
    UV_COMMAND="$uv_cmd"
    uv_version=$("$UV_COMMAND" --version 2>&1 || true)
    echo "  ✓ uv 已就绪 ($uv_version)"
    
    # 如果使用本地 uv，配置镜像源
    local_uv="$PROJECT_ROOT/tools/uv"
    if [[ -f "$local_uv" ]]; then
        set_chinese_mirror
    fi
else
    echo "  ✗ uv 未找到"
    echo ""
    echo "  正在自动下载 uv..."
    
    # 创建 tools 目录
    mkdir -p "$PROJECT_ROOT/tools"
    
    # 确定下载 URL
    os_type="$(uname -s)"
    machine_type="$(uname -m)"
    
    case "$os_type" in
        Linux*)
            case "$machine_type" in
                x86_64)
                    uv_url="https://releases.astral.sh/github/uv/releases/download/0.11.32/uv-x86_64-unknown-linux-gnu.tar.gz"
                    ;;
                aarch64|arm64)
                    uv_url="https://releases.astral.sh/github/uv/releases/download/0.11.32/uv-aarch64-unknown-linux-gnu.tar.gz"
                    ;;
                *)
                    echo "  ✗ 不支持的架构: $machine_type"
                    exit 1
                    ;;
            esac
            ;;
        Darwin*)
            case "$machine_type" in
                x86_64)
                    uv_url="https://releases.astral.sh/github/uv/releases/download/0.11.32/uv-x86_64-apple-darwin.tar.gz"
                    ;;
                arm64|aarch64)
                    uv_url="https://releases.astral.sh/github/uv/releases/download/0.11.32/uv-aarch64-apple-darwin.tar.gz"
                    ;;
                *)
                    echo "  ✗ 不支持的架构: $machine_type"
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo "  ✗ 不支持的操作系统: $os_type"
            echo "  请手动安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
            ;;
    esac
    
    # 下载并解压
    uv_dir="$PROJECT_ROOT/tools"
    uv_tar="$uv_dir/uv.tar.gz"
    
    echo "    下载 uv..."
    curl -LsSf "$uv_url" -o "$uv_tar"
    
    echo "    解压..."
    tar -xzf "$uv_tar" -C "$uv_dir"
    rm -f "$uv_tar"
    
    # 查找 uv 可执行文件
    uv_binary=$(find "$uv_dir" -name "uv" -type f -executable | head -1)
    if [[ -n "$uv_binary" ]]; then
        chmod +x "$uv_binary"
        UV_COMMAND="$uv_binary"
        uv_version=$("$UV_COMMAND" --version 2>&1 || true)
        echo "  ✓ uv 下载成功 ($uv_version)"
        
        # 配置镜像源
        set_chinese_mirror
    else
        echo "  ✗ uv 下载失败"
        echo "  请手动安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi

# ──────────────────────────────────────────
# [2/6] 检查/安装 Python 版本
# ──────────────────────────────────────────
echo "[2/6] 检查 Python 版本 (>=3.12)..."

PYTHON_COMMAND=""

# 先检查系统 Python
if command -v python3 &> /dev/null; then
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "")
    if [[ -n "$python_version" ]]; then
        python_major=$(echo "$python_version" | cut -d. -f1)
        python_minor=$(echo "$python_version" | cut -d. -f2)
        
        if [[ "$python_major" -ge 3 ]] && [[ "$python_minor" -ge 12 ]]; then
            PYTHON_COMMAND="python3"
            echo "  ✓ 系统 Python 可用 (Python $python_version)"
        else
            echo "  ⚠ 系统 Python 版本过低: $python_version (需要 >= 3.12)"
        fi
    fi
fi

# 如果系统 Python 不可用，尝试使用 uv 管理的 Python
if [[ -z "$PYTHON_COMMAND" ]]; then
    echo "  尝试使用 uv 管理 Python..."
    
    # 检查 uv 是否有 Python
    if "$UV_COMMAND" python list 2>/dev/null | grep -q "3\.12"; then
        echo "  ✓ uv 已管理 Python 3.12+"
        PYTHON_COMMAND="$UV_COMMAND run python"
    else
        echo "  正在通过 uv 安装 Python 3.12..."
        
        # 使用 uv 安装 Python
        "$UV_COMMAND" python install 3.12 2>&1 | while read -r line; do
            echo "    $line"
        done
        
        if [[ $? -eq 0 ]]; then
            echo "  ✓ Python 3.12 安装成功"
            PYTHON_COMMAND="$UV_COMMAND run python"
        else
            echo "  ✗ Python 安装失败"
            echo ""
            echo "  请手动安装 Python 3.12+: https://www.python.org/downloads/"
            exit 1
        fi
    fi
fi

# ──────────────────────────────────────────
# [3/6] 安装依赖
# ──────────────────────────────────────────
echo "[3/6] 安装依赖..."

cd "$PROJECT_ROOT/run-flow-skills-mcp"

echo "  正在安装依赖包（使用国内镜像）..."
if ! "$UV_COMMAND" sync 2>&1 | while read -r line; do echo "    $line"; done; then
    echo "  ✗ 依赖安装失败"
    echo ""
    echo "  请尝试手动安装："
    echo "  cd run-flow-skills-mcp"
    echo "  uv sync"
    exit 1
fi
echo "  ✓ 依赖安装完成"

# ──────────────────────────────────────────
# [4/6] 下载 Web 静态资源（可选）
# ──────────────────────────────────────────
echo "[4/6] 下载 Web 静态资源（可选）..."
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
# [5/6] 验证安装
# ──────────────────────────────────────────
echo "[5/6] 验证安装..."

# 验证 MCP Server 入口点可用
"$UV_COMMAND" run run-flow-skills-mcp --help >/dev/null 2>&1 && echo "  ✓ MCP Server 入口点可用" || echo "  ⚠ MCP Server 验证跳过"

# 验证 Web 入口点可用
web_test=$("$UV_COMMAND" run python -c "from run_flow_skills_mcp.web.app import create_app; print('OK')" 2>&1)
if echo "$web_test" | grep -q "OK"; then
    echo "  ✓ Web 可视化模块可用"
else
    echo "  ⚠ Web 可视化模块验证跳过"
fi

# ──────────────────────────────────────────
# [6/6] 安装完成提示
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
