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

# 脚本位于 RunFlowSkills/scripts/build-release.ps1
# $PSScriptRoot = ...\RunFlowSkills\scripts → Split-Path 一次 = ...\RunFlowSkills（项目根）
$projectRoot = $PSScriptRoot | Split-Path
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
    ".trae/skills",
    "run-flow-skills-mcp/src",
    "run-flow-skills-mcp/data/sessions",
    "run-flow-skills-mcp/data/metrics",
    "run-flow-skills-mcp/data/load",
    "run-flow-skills-mcp/data/body_signals",
    "run-flow-skills-mcp/data/decisions",
    "run-flow-skills-mcp/data/plans",
    "scripts",
    "tools"
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
