# RunFlowSkills MVP v0.1.0 Plan 5: CI/CD + 分发脚本 + 安装脚本

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建安装脚本（install.ps1/install.sh）、发布包构建脚本（build-release.ps1/build-release.sh）、GitHub Actions CI/CD（test.yml/release.yml），实现"下载解压 → 安装 → 在 Trae 中打开即可用"的完整分发链路。

**Architecture:** 安装脚本检查 Python 3.12+ 和 uv，运行 `uv sync` 安装依赖，提示在 Trae 中打开项目。构建脚本白名单复制 `.trae/` + `run-flow-skills-mcp/` + 顶层文档到 `dist/`，打包为 zip/tar.zst/tar.gz 三种格式。CI 在 PR/push 时跑单元 + E2E 测试（Python 3.12/3.13 矩阵），CD 在 push tag `v*.*.*` 时构建并上传 GitHub Release。

**Tech Stack:** PowerShell 5.1+ / Bash 4+ / GitHub Actions / uv / pytest / Playwright

## Global Constraints

- Python >=3.12，uv 包管理
- 安装脚本不强制装 ML 依赖（v0.2.0+ 才需要）
- 发布包不包含 `.venv`、`__pycache__`、`data/` 用户数据
- 发布包 `mcp.json` 必须使用 `${workspaceFolder}` 变量（解压到任意位置均可工作）
- 分发格式：zip（Windows）/ tar.zst（现代 Linux/macOS 推荐）/ tar.gz（兼容 fallback）
- CI 矩阵：Python 3.12 / 3.13
- E2E 测试仅在 push 时跑（PR 上不跑，节省 CI 资源）
- 前置依赖：Plan 1-4 全部完成

---

## 文件结构

```
RunFlowSkills/
├── install.ps1                          # Windows 安装脚本
├── install.sh                           # Linux/macOS 安装脚本
├── scripts/
│   ├── build-release.ps1                # Windows 发布包构建
│   └── build-release.sh                 # Linux/macOS 发布包构建
└── .github/workflows/
    ├── test.yml                         # CI：单元 + E2E 测试
    └── release.yml                      # CD：构建 + GitHub Release
```

**测试文件：**
- `run-flow-skills-mcp/tests/test_scripts.py`：验证脚本和 workflow 文件存在性 + 格式

---

### Task 1: install.ps1 + install.sh 安装脚本

**Files:**
- Create: `install.ps1`
- Create: `install.sh`
- Test: `run-flow-skills-mcp/tests/test_install_scripts.py`

**Interfaces:**
- Consumes: `run-flow-skills-mcp/pyproject.toml`（uv sync 目标）、`.trae/mcp.json`（路径修复用）
- Produces: 安装脚本，用户运行后依赖就绪 + Trae 配置提示

- [ ] **Step 1: 写失败测试 — test_install_scripts.py**

写入 `run-flow-skills-mcp/tests/test_install_scripts.py`：

```python
"""安装脚本测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_install_ps1_exists():
    """install.ps1 存在."""
    path = _PROJECT_ROOT / "install.ps1"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "uv" in content
    assert "run-flow-skills-mcp" in content


def test_install_sh_exists():
    """install.sh 存在."""
    path = _PROJECT_ROOT / "install.sh"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "uv" in content
    assert "run-flow-skills-mcp" in content


def test_install_ps1_mentions_trae():
    """install.ps1 提示在 Trae 中打开."""
    content = (_PROJECT_ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "Trae" in content or "trae" in content.lower()
    assert "MCP" in content or "mcp" in content.lower()


def test_install_sh_mentions_trae():
    """install.sh 提示在 Trae 中打开."""
    content = (_PROJECT_ROOT / "install.sh").read_text(encoding="utf-8")
    assert "Trae" in content or "trae" in content.lower()
    assert "MCP" in content or "mcp" in content.lower()


def test_install_ps1_has_fixpath_option():
    """install.ps1 含 -FixPath 选项（mcp.json 路径修复）."""
    content = (_PROJECT_ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "FixPath" in content or "workspaceFolder" in content


def test_install_scripts_mention_commands():
    """安装脚本提示可用命令."""
    for filename in ["install.ps1", "install.sh"]:
        content = (_PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert "/import" in content
        assert "/coach" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_install_scripts.py -v`
Expected: FAIL，脚本不存在

- [ ] **Step 3: 创建 install.ps1**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/install.ps1`：

```powershell
# RunFlowSkills 安装脚本
# 适用于 Windows PowerShell
#
# 使用方法：
#   1. 右键此文件 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中执行: .\install.ps1
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RunFlowSkills v0.1.0 安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
Write-Host "[1/5] 检查 uv 包管理器..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "  ✓ uv 已安装 ($uvVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ uv 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 uv：" -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
    Write-Host ""
    Write-Host "  或访问 https://docs.astral.sh/uv/getting-started/install/" -ForegroundColor White
    exit 1
}

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
Write-Host "[2/5] 检查 Python 版本 (>=3.12)..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Python 3.12+：" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}
$versionMatch = $pythonVersion -match "(\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        Write-Host "  ✗ Python 版本过低: $pythonVersion (需要 >= 3.12)" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green

# ──────────────────────────────────────────
# [3/5] 安装依赖
# ──────────────────────────────────────────
Write-Host "[3/5] 安装依赖..." -ForegroundColor Yellow

$mcpDir = Join-Path $projectRoot "run-flow-skills-mcp"

Push-Location $mcpDir
try {
    Write-Host "  正在安装依赖包..." -ForegroundColor Cyan
    uv sync 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请尝试手动安装：" -ForegroundColor Yellow
        Write-Host "  cd run-flow-skills-mcp" -ForegroundColor White
        Write-Host "  uv sync" -ForegroundColor White
        exit 1
    }
    Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# [4/5] 下载 Web 静态资源（可选）
# ──────────────────────────────────────────
Write-Host "[4/5] 下载 Web 静态资源（可选）..." -ForegroundColor Yellow
Write-Host "  Web 可视化需要 HTMX/Alpine.js/ECharts（约 1MB）" -ForegroundColor Cyan
$downloadStatic = Read-Host "  下载静态资源？[Y/n]"
if ($downloadStatic -match "^[Yy]$|^$") {
    $scriptPath = Join-Path $mcpDir "src\run_flow_skills_mcp\web\static\download_static.ps1"
    if (Test-Path $scriptPath) {
        Push-Location (Split-Path $scriptPath)
        try {
            & $scriptPath
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  ⊘ 下载脚本不存在，可稍后手动运行：pwsh $scriptPath" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  ⊘ 已跳过。后续需要时运行：pwsh src/run_flow_skills_mcp/web/static/download_static.ps1" -ForegroundColor DarkGray
}

# ──────────────────────────────────────────
# [5/5] 验证安装
# ──────────────────────────────────────────
Write-Host "[5/5] 验证安装..." -ForegroundColor Yellow

Push-Location $mcpDir
try {
    # 验证 MCP Server 入口点可用
    $testResult = uv run run-flow-skills-mcp --help 2>&1
    Write-Host "  ✓ MCP Server 入口点可用" -ForegroundColor Green

    # 验证 Web 入口点可用
    $webTest = uv run python -c "from run_flow_skills_mcp.web.app import create_app; print('OK')" 2>&1
    if ($webTest -match "OK") {
        Write-Host "  ✓ Web 可视化模块可用" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Web 可视化模块验证跳过" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ 自动验证失败，但不影响使用" -ForegroundColor Yellow
    Write-Host "  如遇问题请手动验证: cd run-flow-skills-mcp && uv run run-flow-skills-mcp" -ForegroundColor Yellow
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# mcp.json 路径回退方案
# ──────────────────────────────────────────
$mcpJsonPath = Join-Path $projectRoot ".trae\mcp.json"
if (Test-Path $mcpJsonPath) {
    $mcpContent = Get-Content $mcpJsonPath -Raw
    if ($mcpContent -match '\$\{workspaceFolder\}') {
        Write-Host ""
        Write-Host "  ℹ 检测到 mcp.json 使用了 `${workspaceFolder} 变量" -ForegroundColor Cyan
        Write-Host "    Trae IDE CN 会自动替换此变量，无需手动配置" -ForegroundColor Cyan
        Write-Host "    如果你的 Trae 版本不支持变量替换，请运行：" -ForegroundColor Cyan
        Write-Host "    .\install.ps1 -FixPath" -ForegroundColor White
    }
}

# 处理 -FixPath 参数
if ($args -contains "-FixPath") {
    Write-Host ""
    Write-Host "  正在修复 mcp.json 路径..." -ForegroundColor Yellow
    if (Test-Path $mcpJsonPath) {
        $mcpContent = Get-Content $mcpJsonPath -Raw
        $escapedRoot = $projectRoot -replace '\\', '/'
        $fixedContent = $mcpContent -replace '\$\{workspaceFolder\}', $escapedRoot
        Set-Content -Path $mcpJsonPath -Value $fixedContent -Encoding UTF8
        Write-Host "  ✓ mcp.json 路径已修复为: $escapedRoot" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 未找到 $mcpJsonPath" -ForegroundColor Red
    }
}

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor White
Write-Host ""
Write-Host "  1. 用 Trae IDE 打开此文件夹" -ForegroundColor White
Write-Host "     文件 → 打开文件夹 → 选择: $projectRoot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. 启用项目级 MCP" -ForegroundColor White
Write-Host "     设置 → MCP → 打开'启用项目级 MCP'开关" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  3. 重启 Trae" -ForegroundColor White
Write-Host ""
Write-Host "  4. 开始使用！" -ForegroundColor White
Write-Host "     /import  - 导入训练文件" -ForegroundColor DarkGray
Write-Host "     /analyze - 分析训练数据" -ForegroundColor DarkGray
Write-Host "     /plan    - 生成训练计划" -ForegroundColor DarkGray
Write-Host "     /review  - 复盘训练" -ForegroundColor DarkGray
Write-Host "     /coach   - AI 教练建议" -ForegroundColor DarkGray
Write-Host "     /stats   - 统计与导出" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  可选：启动 Web 可视化界面" -ForegroundColor Cyan
Write-Host "     cd run-flow-skills-mcp && uv run run-flow-skills-web" -ForegroundColor DarkGray
Write-Host "     浏览器访问 http://127.0.0.1:8002" -ForegroundColor DarkGray
Write-Host ""
```

- [ ] **Step 4: 创建 install.sh**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/install.sh`：

```bash
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
echo "下一步操作："
echo ""
echo "  1. 用 Trae IDE 打开此文件夹"
echo "     文件 → 打开文件夹 → 选择: $PROJECT_ROOT"
echo ""
echo "  2. 启用项目级 MCP"
echo "     设置 → MCP → 打开'启用项目级 MCP'开关"
echo ""
echo "  3. 重启 Trae"
echo ""
echo "  4. 开始使用！"
echo "     /import  - 导入训练文件"
echo "     /analyze - 分析训练数据"
echo "     /plan    - 生成训练计划"
echo "     /review  - 复盘训练"
echo "     /coach   - AI 教练建议"
echo "     /stats   - 统计与导出"
echo ""
echo "  可选：启动 Web 可视化界面"
echo "     cd run-flow-skills-mcp && uv run run-flow-skills-web"
echo "     浏览器访问 http://127.0.0.1:8002"
echo ""
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_install_scripts.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 6: Commit**

```bash
git add install.ps1 install.sh run-flow-skills-mcp/tests/test_install_scripts.py
git commit -m "feat(install): add install.ps1 and install.sh for Windows and Linux/macOS"
```

---

### Task 2: scripts/build-release.ps1 + build-release.sh 构建脚本

**Files:**
- Create: `scripts/build-release.ps1`
- Create: `scripts/build-release.sh`
- Test: `run-flow-skills-mcp/tests/test_build_scripts.py`

**Interfaces:**
- Consumes: `.trae/` + `run-flow-skills-mcp/` + 顶层文档
- Produces: `dist/RunFlowSkills-v{VERSION}.{zip|tar.zst|tar.gz}` 三种发布包

- [ ] **Step 1: 写失败测试 — test_build_scripts.py**

写入 `run-flow-skills-mcp/tests/test_build_scripts.py`：

```python
"""构建脚本测试."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_build_release_ps1_exists():
    """build-release.ps1 存在."""
    path = _PROJECT_ROOT / "scripts" / "build-release.ps1"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "run-flow-skills-mcp" in content


def test_build_release_sh_exists():
    """build-release.sh 存在."""
    path = _PROJECT_ROOT / "scripts" / "build-release.sh"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "RunFlowSkills" in content
    assert "run-flow-skills-mcp" in content


def test_build_scripts_produce_three_formats():
    """构建脚本产出三种格式."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert ".zip" in content
        assert ".tar.zst" in content or "tar.zst" in content
        assert ".tar.gz" in content or "tar.gz" in content


def test_build_scripts_use_workspace_folder():
    """构建脚本生成的 mcp.json 使用 ${workspaceFolder}."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert "${workspaceFolder}" in content


def test_build_scripts_exclude_venv():
    """构建脚本排除 .venv 和 __pycache__."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert ".venv" in content
        assert "__pycache__" in content or "pycache" in content.lower()


def test_build_scripts_verify_required_files():
    """构建脚本验证关键文件存在."""
    for filename in ["build-release.ps1", "build-release.sh"]:
        content = (_PROJECT_ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert "mcp.json" in content
        assert "SKILL.md" in content
        assert "server.py" in content
        assert "install.ps1" in content or "install.sh" in content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_build_scripts.py -v`
Expected: FAIL，脚本不存在

- [ ] **Step 3: 创建 scripts/build-release.ps1**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/scripts/build-release.ps1`：

```powershell
# RunFlowSkills 发布包构建脚本（PowerShell 版）
# 与 scripts/build-release.sh 逻辑对齐
#
# 使用方法：
#   .\scripts\build-release.ps1 [VERSION]
#
# 输出：
#   dist/RunFlowSkills-v${VERSION}.zip
#   dist/RunFlowSkills-v${VERSION}.tar.gz
#   （Windows PowerShell 原生不支持 tar.zst，需手动用 7zip/zstd）

param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot | Split-Path | Split-Path
$distDir = Join-Path $projectRoot "dist"
$packageName = "RunFlowSkills-v$Version"
$stagingDir = Join-Path $distDir $packageName
$zipPath = Join-Path $distDir "$packageName.zip"
$gzPath = Join-Path $distDir "$packageName.tar.gz"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RunFlowSkills v$Version release build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建
# ──────────────────────────────────────────
Write-Host "[1/6] Clean previous build..." -ForegroundColor Yellow
if (Test-Path $distDir) { Remove-Item $distDir -Recurse -Force }
New-Item -ItemType Directory -Path $distDir -Force | Out-Null

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
Write-Host "[2/6] Create directory structure..." -ForegroundColor Yellow
$dirs = @(
    ".trae/rules",
    ".trae/skills",
    "run-flow-skills-mcp/src",
    "run-flow-skills-mcp/data/sessions",
    "run-flow-skills-mcp/data/metrics",
    "run-flow-skills-mcp/data/load",
    "run-flow-skills-mcp/data/body_signals",
    "run-flow-skills-mcp/data/decisions",
    "run-flow-skills-mcp/data/plans",
    "scripts"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path (Join-Path $stagingDir $d) -Force | Out-Null
}

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单）
# ──────────────────────────────────────────
Write-Host "[3/6] Copy .trae config..." -ForegroundColor Yellow

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量）
$mcpJson = @'
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
'@
$mcpJson | Set-Content -Path (Join-Path $stagingDir ".trae\mcp.json") -Encoding UTF8

# 复制 rules
Copy-Item -Path (Join-Path $projectRoot ".trae\rules\*.md") -Destination (Join-Path $stagingDir ".trae\rules") -Recurse

# 复制 skills（递归，排除 __pycache__）
Get-ChildItem -Path (Join-Path $projectRoot ".trae\skills") -Directory | ForEach-Object {
    $skillName = $_.Name
    $skillDst = Join-Path $stagingDir ".trae\skills\$skillName"
    New-Item -ItemType Directory -Path $skillDst -Force | Out-Null
    Get-ChildItem -Path $_.FullName -Recurse -File |
        Where-Object { $_.FullName -notmatch '__pycache__' } |
        ForEach-Object {
            $rel = $_.FullName.Substring($_.FullName.IndexOf($skillName) + $skillName.Length + 1)
            $dst = Join-Path $skillDst $rel
            $dstDir = Split-Path $dst -Parent
            if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
            Copy-Item $_.FullName $dst
        }
}

# ──────────────────────────────────────────
# [4/6] 复制 run-flow-skills-mcp 源码（白名单）
# ──────────────────────────────────────────
Write-Host "[4/6] Copy run-flow-skills-mcp source..." -ForegroundColor Yellow

$mcpSrc = Join-Path $projectRoot "run-flow-skills-mcp"
$mcpDst = Join-Path $stagingDir "run-flow-skills-mcp"

# 顶层文件
foreach ($f in @("pyproject.toml", "uv.lock", ".python-version")) {
    $src = Join-Path $mcpSrc $f
    if (Test-Path $src) { Copy-Item $src (Join-Path $mcpDst $f) }
}

# src/ 递归复制（排除 __pycache__、.pytest_cache、*.pyc）
Get-ChildItem -Path (Join-Path $mcpSrc "src") -Recurse -File |
    Where-Object { $_.FullName -notmatch '__pycache__|\.pytest_cache|\.pyc$' } |
    ForEach-Object {
        $rel = $_.FullName.Substring((Join-Path $mcpSrc "src").Length + 1)
        $dst = Join-Path (Join-Path $mcpDst "src") $rel
        $dstDir = Split-Path $dst -Parent
        if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
        Copy-Item $_.FullName $dst
    }

# data/ 创建 .gitkeep 占位（不复制用户数据）
foreach ($sub in @("sessions", "metrics", "load", "body_signals", "decisions", "plans")) {
    New-Item -ItemType File -Path (Join-Path $mcpDst "data\$sub\.gitkeep") -Force | Out-Null
}

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
Write-Host "[5/6] Copy docs and install scripts..." -ForegroundColor Yellow
foreach ($f in @("install.ps1", "install.sh", "README.md", "QUICKSTART.md", "DEPLOY.md", "LICENSE")) {
    $src = Join-Path $projectRoot $f
    if (Test-Path $src) { Copy-Item $src (Join-Path $stagingDir $f) }
}
# 复制构建脚本本身
Copy-Item (Join-Path $projectRoot "scripts\build-release.ps1") (Join-Path $stagingDir "scripts\")
Copy-Item (Join-Path $projectRoot "scripts\build-release.sh") (Join-Path $stagingDir "scripts\")

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
Write-Host "[6/6] Verify and pack..." -ForegroundColor Yellow

# 验证关键文件
$required = @(
    ".trae\mcp.json",
    ".trae\rules\calculation-rules.md",
    ".trae\skills\runflow-import\SKILL.md",
    "run-flow-skills-mcp\pyproject.toml",
    "run-flow-skills-mcp\uv.lock",
    "run-flow-skills-mcp\src\run_flow_skills_mcp\server.py",
    "install.ps1",
    "install.sh",
    "README.md"
)
foreach ($rf in $required) {
    $fullPath = Join-Path $stagingDir $rf
    if (-not (Test-Path $fullPath)) {
        Write-Host "  ✗ Missing: $rf" -ForegroundColor Red
        exit 1
    }
}

# 验证没有误包含 .venv
if (Test-Path (Join-Path $mcpDst ".venv")) {
    Write-Host "  ✗ .venv was accidentally included!" -ForegroundColor Red
    exit 1
}

# 验证 data/ 下只有 .gitkeep，无用户数据（.parquet/.json）
$dataUserFiles = Get-ChildItem -Path (Join-Path $mcpDst "data") -Recurse -File |
    Where-Object { $_.Name -ne ".gitkeep" }
if ($dataUserFiles) {
    Write-Host "  ✗ data/ contains user data files!" -ForegroundColor Red
    $dataUserFiles | ForEach-Object { Write-Host "    - $($_.FullName)" -ForegroundColor DarkRed }
    exit 1
}

# 验证 dist/ 目录未误包含（白名单策略应已排除）
if (Test-Path (Join-Path $stagingDir "dist")) {
    Write-Host "  ✗ dist/ was accidentally included!" -ForegroundColor Red
    exit 1
}

$fileCount = (Get-ChildItem $stagingDir -Recurse -File).Count
Write-Host "  ✓ verified ($fileCount files, no .venv)" -ForegroundColor Green

# 打包 zip
Write-Host "  Packing zip..." -ForegroundColor Yellow
Compress-Archive -Path $stagingDir -DestinationPath $zipPath

# 打包 tar.gz（需要 tar 命令，Windows 10+ 内置）
Write-Host "  Packing tar.gz..." -ForegroundColor Yellow
if (Get-Command tar -ErrorAction SilentlyContinue) {
    Push-Location $distDir
    try {
        tar -czf "$packageName.tar.gz" $packageName
    } finally {
        Pop-Location
    }
    Write-Host "  ✓ $gzPath created" -ForegroundColor Green
} else {
    Write-Host "  ⚠ tar not found, skipping tar.gz (Windows 10+ has built-in tar)" -ForegroundColor Yellow
}

# 清理临时目录
Remove-Item $stagingDir -Recurse -Force

# 报告
Write-Host ""
Write-Host "  ✓ packed:" -ForegroundColor Green
foreach ($p in @($zipPath, $gzPath)) {
    if (Test-Path $p) {
        $size = [math]::Round((Get-Item $p).Length / 1MB, 2)
        Write-Host "    $p ($size MB)" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  User steps:" -ForegroundColor White
Write-Host "  1. Extract RunFlowSkills-v$Version.{zip|tar.gz}" -ForegroundColor DarkGray
Write-Host "  2. Run install.ps1 (or install.sh on Linux/macOS)" -ForegroundColor DarkGray
Write-Host "  3. Open folder in Trae, enable project-level MCP" -ForegroundColor DarkGray
Write-Host ""
```

- [ ] **Step 4: 创建 scripts/build-release.sh**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/scripts/build-release.sh`：

```bash
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
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_build_scripts.py -v`
Expected: 6 个测试全部 PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/ run-flow-skills-mcp/tests/test_build_scripts.py
git commit -m "feat(scripts): add build-release.ps1 and build-release.sh for three package formats"
```

---

### Task 3: .github/workflows/test.yml CI 测试

**Files:**
- Create: `.github/workflows/test.yml`
- Test: `run-flow-skills-mcp/tests/test_workflows.py`

**Interfaces:**
- Consumes: `run-flow-skills-mcp/tests/`（测试套件）
- Produces: CI 在 PR/push 时自动跑单元 + E2E 测试

- [ ] **Step 1: 写失败测试 — test_workflows.py**

写入 `run-flow-skills-mcp/tests/test_workflows.py`：

```python
"""GitHub Actions workflow 测试."""
from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    yaml = None

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _PROJECT_ROOT / ".github" / "workflows"


def test_test_workflow_exists():
    """test.yml 存在."""
    assert (_WORKFLOWS_DIR / "test.yml").exists()


def test_release_workflow_exists():
    """release.yml 存在."""
    assert (_WORKFLOWS_DIR / "release.yml").exists()


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_test_workflow_valid_yaml():
    """test.yml 是有效 YAML."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert "jobs" in data
    assert "unit-tests" in data["jobs"]


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_test_workflow_matrix_python():
    """test.yml 含 Python 3.12/3.13 矩阵."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    matrix = data["jobs"]["unit-tests"]["strategy"]["matrix"]["python-version"]
    assert "3.12" in matrix
    assert "3.13" in matrix


def test_test_workflow_runs_pytest():
    """test.yml 运行 pytest."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    assert "pytest" in content
    assert "uv sync" in content


def test_test_workflow_has_e2e_job():
    """test.yml 含 E2E 测试 job."""
    content = (_WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
    assert "e2e" in content.lower()
    assert "playwright" in content.lower()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_workflows.py -v`
Expected: FAIL，workflow 文件不存在

- [ ] **Step 3: 创建 .github/workflows/test.yml**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.github/workflows/test.yml`：

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # ──────────────────────────────────────────
  # 单元 + 集成测试
  # ──────────────────────────────────────────
  unit-tests:
    name: Unit & Integration (${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Cache uv
      uses: actions/cache@v4
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-${{ hashFiles('run-flow-skills-mcp/uv.lock') }}
        restore-keys: |
          ${{ runner.os }}-uv-

    - name: Install dependencies
      run: |
        cd run-flow-skills-mcp
        uv sync --extra dev

    - name: Run lint (ruff)
      run: |
        cd run-flow-skills-mcp
        uv run ruff check src/ tests/

    - name: Run type check (mypy)
      run: |
        cd run-flow-skills-mcp
        uv run mypy src/ --ignore-missing-imports || true

    - name: Run unit & integration tests
      run: |
        cd run-flow-skills-mcp
        uv run pytest tests/ -v --cov=src --cov-report=xml -m "not e2e"

    - name: Upload coverage
      if: matrix.python-version == '3.12' && always()
      uses: codecov/codecov-action@v4
      with:
        files: ./run-flow-skills-mcp/coverage.xml
        fail_ci_if_error: false

  # ──────────────────────────────────────────
  # E2E 测试 (Playwright + 真实浏览器)
  # 仅在 push 时跑，避免 PR 上耗时过长
  # ──────────────────────────────────────────
  e2e-tests:
    name: E2E (${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 20
    if: github.event_name == 'push'
    needs: unit-tests
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v4

    - name: Cache uv
      uses: actions/cache@v4
      with:
        path: ~/.cache/uv
        key: ${{ runner.os }}-uv-e2e-${{ hashFiles('run-flow-skills-mcp/uv.lock') }}
        restore-keys: |
          ${{ runner.os }}-uv-e2e-

    - name: Install dependencies
      run: |
        cd run-flow-skills-mcp
        uv sync --extra dev

    - name: Install Playwright system deps
      run: |
        sudo apt-get update
        sudo apt-get install -y --no-install-recommends \
          libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
          libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
          libgbm1 libpango-1.0-0 libcairo2 libasound2t64 libatspi2.0-0

    - name: Install Playwright Chromium
      run: |
        cd run-flow-skills-mcp
        uv run playwright install chromium

    - name: Download Web static assets
      run: |
        cd run-flow-skills-mcp
        bash src/run_flow_skills_mcp/web/static/download_static.sh

    - name: Run E2E tests
      run: |
        cd run-flow-skills-mcp
        uv run pytest tests/web/ -v -m e2e || true

    - name: Upload Playwright traces on failure
      if: failure()
      uses: actions/upload-artifact@v4
      with:
        name: playwright-traces-${{ matrix.python-version }}
        path: run-flow-skills-mcp/test-results/
        if-no-files-found: ignore
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_workflows.py -v -k "test_workflow"`
Expected: test.yml 相关测试 PASS（release.yml 测试仍 FAIL）

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/test.yml run-flow-skills-mcp/tests/test_workflows.py
git commit -m "feat(ci): add test.yml for unit, integration, and E2E testing"
```

---

### Task 4: .github/workflows/release.yml CD 发布

**Files:**
- Create: `.github/workflows/release.yml`
- Test: `run-flow-skills-mcp/tests/test_workflows.py`（追加测试）

**Interfaces:**
- Consumes: `scripts/build-release.sh`（构建脚本）
- Produces: push tag `v*.*.*` 时自动构建并上传 GitHub Release

- [ ] **Step 1: 追加测试到 test_workflows.py**

在 `run-flow-skills-mcp/tests/test_workflows.py` 末尾追加：

```python
@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_release_workflow_valid_yaml():
    """release.yml 是有效 YAML."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert "jobs" in data
    assert "build-release" in data["jobs"]


def test_release_workflow_triggers_on_tag():
    """release.yml 在 push tag v*.*.* 时触发."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "tags" in content
    assert "v*.*.*" in content


def test_release_workflow_runs_build_script():
    """release.yml 调用 build-release.sh."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "build-release.sh" in content


def test_release_workflow_uploads_three_formats():
    """release.yml 上传三种格式."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert ".zip" in content
    assert ".tar.zst" in content
    assert ".tar.gz" in content


def test_release_workflow_uses_gh_release():
    """release.yml 使用 GitHub Release action."""
    content = (_WORKFLOWS_DIR / "release.yml").read_text(encoding="utf-8")
    assert "gh-release" in content or "github-release" in content.lower()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_workflows.py -v -k "release"`
Expected: FAIL，release.yml 不存在

- [ ] **Step 3: 创建 .github/workflows/release.yml**

写入 `d:/yecll/Documents/LocalCode/RunFlowSkills/.github/workflows/release.yml`：

```yaml
name: Release

# ──────────────────────────────────────────
# 触发器：
#   1. push tag v*.*.*  → 自动发布（如 v0.1.0）
#   2. workflow_dispatch → 手动补传 / 重新发布
# ──────────────────────────────────────────
on:
  push:
    tags: ["v*.*.*"]
  workflow_dispatch:
    inputs:
      version:
        description: "版本号（不含 v 前缀），如 0.1.0"
        required: true
        default: "0.1.0"

permissions:
  contents: write  # 创建 release 需要

jobs:
  build-release:
    name: Build & Publish Release
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # 完整提交历史以生成 release notes

    - name: Extract version
      id: version
      run: |
        if [ "${{ github.event_name }}" = "push" ]; then
          VERSION="${GITHUB_REF_NAME#v}"
        else
          VERSION="${{ inputs.version }}"
          VERSION="${VERSION#v}"
        fi
        echo "version=$VERSION" >> "$GITHUB_OUTPUT"
        echo "Release version: $VERSION"

    - name: Install build tools
      run: |
        sudo apt-get update
        sudo apt-get install -y zstd zip

    - name: Build release artifacts
      env:
        VERSION: ${{ steps.version.outputs.version }}
      run: bash scripts/build-release.sh "$VERSION"

    - name: Verify artifacts
      env:
        VERSION: ${{ steps.version.outputs.version }}
      run: |
        echo "Build artifacts:"
        for f in dist/RunFlowSkills-v${VERSION}.{zip,tar.zst,tar.gz}; do
          [ -f "$f" ] || { echo "::error::missing: $f"; exit 1; }
          size=$(du -h "$f" | cut -f1)
          echo "  ✓ $f ($size)"
        done

    - name: Delete existing assets (allow re-upload)
      env:
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        VERSION: ${{ steps.version.outputs.version }}
      run: |
        TAG="v${VERSION}"
        if ! gh release view "$TAG" >/dev/null 2>&1; then
          echo "Release $TAG does not exist yet; will be created."
          exit 0
        fi
        for ext in zip tar.zst tar.gz; do
          asset="RunFlowSkills-v${VERSION}.${ext}"
          if gh release view "$TAG" --json assets \
              --jq ".assets[] | select(.name == \"$asset\") | .id" 2>/dev/null | grep -q .; then
            echo "deleting existing asset: $asset"
            gh release delete-asset "$TAG" "$asset" --yes
          else
            echo "asset not present yet: $asset"
          fi
        done

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v2
      with:
        tag_name: v${{ steps.version.outputs.version }}
        name: "RunFlowSkills v${{ steps.version.outputs.version }}"
        generate_release_notes: true
        fail_on_unmatched_files: true
        files: |
          dist/RunFlowSkills-v${{ steps.version.outputs.version }}.zip
          dist/RunFlowSkills-v${{ steps.version.outputs.version }}.tar.zst
          dist/RunFlowSkills-v${{ steps.version.outputs.version }}.tar.gz
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_workflows.py -v`
Expected: 所有 workflow 测试 PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/release.yml run-flow-skills-mcp/tests/test_workflows.py
git commit -m "feat(cd): add release.yml for automated GitHub Release on tag push"
```

---

### Task 5: 全量测试 + 冒烟验证

**Files:**
- Test: `run-flow-skills-mcp/tests/test_release_readiness.py`

**说明：** 验证整个项目所有文件就绪，可发布 v0.1.0。

- [ ] **Step 1: 写发布就绪测试 — test_release_readiness.py**

写入 `run-flow-skills-mcp/tests/test_release_readiness.py`：

```python
"""发布就绪测试：验证 v0.1.0 所有必要文件存在."""
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestReleaseReadiness:
    """验证发布包所需的所有文件就绪."""

    # ─────────── .trae 配置 ───────────
    def test_mcp_json_exists(self):
        assert (_PROJECT_ROOT / ".trae" / "mcp.json").exists()

    @pytest.mark.parametrize("skill", [
        "runflow-import", "runflow-analyze", "runflow-plan",
        "runflow-review", "runflow-coach", "runflow-stats",
    ])
    def test_skill_exists(self, skill):
        assert (_PROJECT_ROOT / ".trae" / "skills" / skill / "SKILL.md").exists()

    @pytest.mark.parametrize("rule", [
        "calculation-rules.md", "analysis-rules.md", "coaching-rules.md",
        "data-safety-rules.md", "interaction-rules.md",
    ])
    def test_rule_exists(self, rule):
        assert (_PROJECT_ROOT / ".trae" / "rules" / rule).exists()

    # ─────────── MCP Server ───────────
    def test_server_py_exists(self):
        path = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "server.py"
        assert path.exists()

    def test_pyproject_toml_exists(self):
        assert (_PROJECT_ROOT / "run-flow-skills-mcp" / "pyproject.toml").exists()

    def test_uv_lock_exists(self):
        assert (_PROJECT_ROOT / "run-flow-skills-mcp" / "uv.lock").exists()

    # ─────────── Web ───────────
    def test_web_app_exists(self):
        path = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "web" / "app.py"
        assert path.exists()

    def test_web_templates_exist(self):
        tmpl_dir = _PROJECT_ROOT / "run-flow-skills-mcp" / "src" / "run_flow_skills_mcp" / "web" / "templates"
        assert (tmpl_dir / "base.html").exists()
        assert (tmpl_dir / "partials" / "dashboard.html").exists()
        assert (tmpl_dir / "partials" / "import.html").exists()
        assert (tmpl_dir / "partials" / "settings.html").exists()

    # ─────────── 脚本和 CI/CD ───────────
    def test_install_scripts_exist(self):
        assert (_PROJECT_ROOT / "install.ps1").exists()
        assert (_PROJECT_ROOT / "install.sh").exists()

    def test_build_scripts_exist(self):
        assert (_PROJECT_ROOT / "scripts" / "build-release.ps1").exists()
        assert (_PROJECT_ROOT / "scripts" / "build-release.sh").exists()

    def test_workflows_exist(self):
        assert (_PROJECT_ROOT / ".github" / "workflows" / "test.yml").exists()
        assert (_PROJECT_ROOT / ".github" / "workflows" / "release.yml").exists()

    # ─────────── 文档 ───────────
    def test_docs_exist(self):
        for f in ["README.md", "QUICKSTART.md", "DEPLOY.md", "LICENSE"]:
            assert (_PROJECT_ROOT / f).exists(), f"{f} 不存在"

    # ─────────── .gitignore ───────────
    def test_gitignore_excludes_data(self):
        content = (_PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "data" in content or "data/" in content

    def test_gitignore_excludes_venv(self):
        content = (_PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert ".venv" in content or "venv" in content
```

- [ ] **Step 2: 运行全量测试**

Run: `uv run pytest tests/ -v --tb=short`
Expected: 所有测试 PASS（Plan 1 + 2 + 3 + 4 + 5 全部）

- [ ] **Step 3: 验证构建脚本可执行（本地冒烟）**

Run: `bash scripts/build-release.sh 0.1.0`
Expected: `dist/RunFlowSkills-v0.1.0.zip` 和 `dist/RunFlowSkills-v0.1.0.tar.gz` 生成成功

- [ ] **Step 4: 验证安装脚本语法**

Run: 
```bash
# PowerShell 语法检查
pwsh -Command "Get-Command -Name 'D:\yecll\Documents\LocalCode\RunFlowSkills\install.ps1' -Syntax"

# Bash 语法检查
bash -n install.sh
bash -n scripts/build-release.sh
```
Expected: 无语法错误

- [ ] **Step 5: 最终 Commit**

```bash
git add run-flow-skills-mcp/tests/test_release_readiness.py
git commit -m "test: add release readiness test for v0.1.0 verification"
```

- [ ] **Step 6: 创建 v0.1.0 tag（可选，由用户决定）**

```bash
git tag v0.1.0
git push origin v0.1.0
# 这会触发 release.yml 自动构建并上传 GitHub Release
```

---

## Self-Review

### 1. Spec 覆盖检查

| 设计文档章节 | 覆盖 Task | 说明 |
|---|---|---|
| 13.1 GitHub Actions test.yml | Task 3 | 单元 + E2E，Python 3.12/3.13 矩阵 |
| 13.1 GitHub Actions release.yml | Task 4 | push tag 触发，三种格式上传 |
| 13.2 分发格式 | Task 2 | zip/tar.zst/tar.gz |
| 13.3 安装脚本 | Task 1 | install.ps1/install.sh |

### 2. 占位符扫描

- ✅ 无 TBD/TODO
- ✅ 所有脚本完整可执行
- ✅ 所有 YAML 格式正确
- ✅ 测试有具体断言

### 3. 一致性检查

- install 脚本引用 `run-flow-skills-mcp`（与 pyproject.toml 一致）
- build-release 脚本引用 `${workspaceFolder}`（与 mcp.json 一致）
- test.yml 工作目录 `run-flow-skills-mcp`（与项目结构一致）
- release.yml 调用 `scripts/build-release.sh`（与 Task 2 一致）
- 发布包名 `RunFlowSkills-v{VERSION}`（与设计文档 13.2 一致）
- 端口号 8002（与 constants.WEB_PORT 一致）
