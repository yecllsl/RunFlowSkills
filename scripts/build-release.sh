#!/usr/bin/env bash
# RunFlowSkills 发布包构建脚本（bash 版）
# 与 scripts/build-release.ps1 逻辑对齐
#
# 使用方法：
#   ./scripts/build-release.sh [VERSION]
#
# 输出：
#   dist/RunFlowSkills-v${VERSION}.zip
#   dist/RunFlowSkills-v${VERSION}.tar.zst
#   dist/RunFlowSkills-v${VERSION}.tar.gz

set -euo pipefail

VERSION="${1:-0.1.0}"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
PACKAGE_NAME="RunFlowSkills-v$VERSION"
STAGING_DIR="$DIST_DIR/$PACKAGE_NAME"
ZIP_PATH="$DIST_DIR/$PACKAGE_NAME.zip"
ZST_PATH="$DIST_DIR/$PACKAGE_NAME.tar.zst"
GZ_PATH="$DIST_DIR/$PACKAGE_NAME.tar.gz"

# ──────────────────────────────────────────
# 颜色输出
# ──────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; NC=''
fi
log_step() { echo -e "${YELLOW}[build]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[ok]${NC}    $1"; }
log_err()  { echo -e "${RED}[err]${NC}   $1" >&2; }

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  RunFlowSkills v$VERSION release build${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建
# ──────────────────────────────────────────
log_step "[1/6] Clean previous build..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
log_ok "cleaned"

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
log_step "[2/6] Create directory structure..."
mkdir -p "$STAGING_DIR/.trae/rules"
mkdir -p "$STAGING_DIR/.trae/skills"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/src"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/sessions"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/metrics"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/load"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/body_signals"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/decisions"
mkdir -p "$STAGING_DIR/run-flow-skills-mcp/data/plans"
mkdir -p "$STAGING_DIR/scripts"
log_ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单）
# ──────────────────────────────────────────
log_step "[3/6] Copy .trae config..."

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量）
cat > "$STAGING_DIR/.trae/mcp.json" <<'EOF'
{
  "mcpServers": {
    "run-flow-skills-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/run-flow-skills-mcp",
        "run-flow-skills-mcp"
      ]
    }
  }
}
EOF

# 复制 rules
if [ -d "$PROJECT_ROOT/.trae/rules" ]; then
    (cd "$PROJECT_ROOT/.trae/rules" && find . -maxdepth 1 -type f -print0) | \
        while IFS= read -r -d '' rel; do
            rel="${rel#./}"
            cp "$PROJECT_ROOT/.trae/rules/$rel" "$STAGING_DIR/.trae/rules/$rel"
        done
fi

# 复制 skills（递归，排除 __pycache__）
if [ -d "$PROJECT_ROOT/.trae/skills" ]; then
    for skill_dir in "$PROJECT_ROOT/.trae/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        skill_dst="$STAGING_DIR/.trae/skills/$skill_name"
        mkdir -p "$skill_dst"
        (cd "$skill_dir" && find . -mindepth 1 -type f ! -path '*/__pycache__/*' -print0) | \
            while IFS= read -r -d '' rel; do
                rel="${rel#./}"
                dst="$skill_dst/$rel"
                mkdir -p "$(dirname "$dst")"
                cp "$skill_dir/$rel" "$dst"
            done
    done
fi
log_ok ".trae config copied"

# ──────────────────────────────────────────
# [4/6] 复制 run-flow-skills-mcp 源码（白名单）
# ──────────────────────────────────────────
log_step "[4/6] Copy run-flow-skills-mcp source..."

MCP_SRC="$PROJECT_ROOT/run-flow-skills-mcp"
MCP_DST="$STAGING_DIR/run-flow-skills-mcp"

# 顶层文件
for f in pyproject.toml uv.lock .python-version; do
    [ -f "$MCP_SRC/$f" ] && cp "$MCP_SRC/$f" "$MCP_DST/$f"
done

# src/ 递归复制（排除 __pycache__、.pytest_cache、*.pyc）
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
        "$MCP_SRC/src/" "$MCP_DST/src/"
else
    (cd "$MCP_SRC/src" && find . -type f \
        ! -path '*/__pycache__/*' ! -path '*/.pytest_cache/*' ! -name '*.pyc' -print0) | \
        while IFS= read -r -d '' rel; do
            rel="${rel#./}"
            dst="$MCP_DST/src/$rel"
            mkdir -p "$(dirname "$dst")"
            cp "$MCP_SRC/src/$rel" "$dst"
        done
fi

# data/ 创建 .gitkeep 占位
for sub in sessions metrics load body_signals decisions plans; do
    touch "$MCP_DST/data/$sub/.gitkeep"
done
log_ok "source copied"

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
log_step "[5/6] Copy docs and install scripts..."
for f in install.ps1 install.sh README.md QUICKSTART.md DEPLOY.md LICENSE; do
    [ -f "$PROJECT_ROOT/$f" ] && cp "$PROJECT_ROOT/$f" "$STAGING_DIR/$f"
done
# 复制构建脚本
cp "$PROJECT_ROOT/scripts/build-release.ps1" "$STAGING_DIR/scripts/"
cp "$PROJECT_ROOT/scripts/build-release.sh" "$STAGING_DIR/scripts/"
log_ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
log_step "[6/6] Verify and pack..."

# 验证关键文件
required=(
    ".trae/mcp.json"
    ".trae/rules/calculation-rules.md"
    ".trae/skills/runflow-import/SKILL.md"
    "run-flow-skills-mcp/pyproject.toml"
    "run-flow-skills-mcp/uv.lock"
    "run-flow-skills-mcp/src/run_flow_skills_mcp/server.py"
    "install.ps1"
    "install.sh"
    "README.md"
)
missing=()
for rf in "${required[@]}"; do
    [ -f "$STAGING_DIR/$rf" ] || missing+=("$rf")
done
if [ ${#missing[@]} -gt 0 ]; then
    log_err "Missing required files:"
    for m in "${missing[@]}"; do log_err "  $m"; done
    exit 1
fi

# 验证没有误包含 .venv
if [ -d "$STAGING_DIR/run-flow-skills-mcp/.venv" ]; then
    log_err ".venv was accidentally included! Aborting."
    exit 1
fi

# 验证 data/ 下只有 .gitkeep，无用户数据（.parquet/.json）
data_user_files=$(find "$STAGING_DIR/run-flow-skills-mcp/data" -type f ! -name '.gitkeep' 2>/dev/null)
if [ -n "$data_user_files" ]; then
    log_err "data/ contains user data files:"
    echo "$data_user_files" | while read -r f; do log_err "  $f"; done
    exit 1
fi

# 验证 dist/ 目录未误包含（白名单策略应已排除）
if [ -d "$STAGING_DIR/dist" ]; then
    log_err "dist/ was accidentally included! Aborting."
    exit 1
fi

file_count=$(find "$STAGING_DIR" -type f | wc -l)
log_ok "verified ($file_count files, no .venv, no user data)"

# 打包 zip
log_step "Packing zip..."
if ! command -v zip >/dev/null 2>&1; then
    log_err "zip not found. Linux: apt-get install zip; macOS: brew install zip"
    exit 1
fi
(cd "$DIST_DIR" && zip -qr "$ZIP_PATH" "$PACKAGE_NAME")

# 打包 tar.zst
log_step "Packing tar.zst..."
if command -v zstd >/dev/null 2>&1; then
    tar -C "$DIST_DIR" -cf - --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
        "$PACKAGE_NAME" | zstd -3 -q -o "$ZST_PATH"
else
    log_err "zstd not found. Linux: apt-get install zstd; macOS: brew install zstd"
    log_err "  Skipping tar.zst (tar.gz still available)"
fi

# 打包 tar.gz
log_step "Packing tar.gz..."
tar -C "$DIST_DIR" -czf "$GZ_PATH" "$PACKAGE_NAME"

# 清理临时目录
rm -rf "$STAGING_DIR"

# 报告
echo ""
log_ok "packed:"
for f in "$ZIP_PATH" "$ZST_PATH" "$GZ_PATH"; do
    [ -f "$f" ] || continue
    size=$(du -h "$f" | cut -f1)
    echo -e "  ${CYAN}$f${NC} ($size)"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Package: ${CYAN}$PACKAGE_NAME${NC}"
echo -e "  Files:   ${CYAN}$file_count${NC}"
echo ""
echo "  User steps:"
echo "  1. Extract RunFlowSkills-v$VERSION.{zip|tar.zst|tar.gz}"
echo "  2. Run install.ps1 (or install.sh on Linux/macOS)"
echo "  3. Open folder in Trae, enable project-level MCP"
echo ""
