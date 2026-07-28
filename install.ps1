# RunFlowSkills 安装脚本
# 适用于 Windows PowerShell
#
# 使用方法：
#   1. 右键此文件 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中执行: .\install.ps1
#
# 特性：
#   - 自动使用项目内 uv.exe（无需预装）
#   - 自动下载 Python 3.12+（如未安装）
#   - 使用国内镜像加速依赖安装

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RunFlowSkills v0.1.1 安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# ──────────────────────────────────────────
# 辅助函数：获取 uv 命令路径
# ──────────────────────────────────────────
function Get-UvCommand {
    # 优先使用系统 uv
    $systemUv = Get-Command uv -ErrorAction SilentlyContinue
    if ($systemUv) {
        return $systemUv.Source
    }
    
    # 回退到项目内 uv.exe
    $localUv = Join-Path $projectRoot "tools\uv.exe"
    if (Test-Path $localUv) {
        return $localUv
    }
    
    # 都没有，返回空
    return $null
}

# ──────────────────────────────────────────
# 辅助函数：配置国内镜像源
# ──────────────────────────────────────────
function Set-ChineseMirror {
    param([string]$UvCommand)
    
    Write-Host "  配置国内镜像源..." -ForegroundColor Cyan
    
    # 创建 uv.toml 配置文件（如果不存在）
    $uvTomlPath = Join-Path $projectRoot "run-flow-skills-mcp\uv.toml"
    $uvTomlContent = @"
# uv 国内镜像源配置
[[index]]
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true

[pip]
index-url = "https://mirrors.aliyun.com/pypi/simple/"
"@
    
    if (-not (Test-Path $uvTomlPath)) {
        $uvTomlContent | Set-Content -Path $uvTomlPath -Encoding UTF8
        Write-Host "    ✓ 已创建 uv.toml 配置文件" -ForegroundColor Green
    } else {
        Write-Host "    ⊘ uv.toml 已存在，跳过" -ForegroundColor DarkGray
    }
}

# ──────────────────────────────────────────
# [1/6] 检查并准备 uv
# ──────────────────────────────────────────
Write-Host "[1/6] 检查 uv 包管理器..." -ForegroundColor Yellow

$uvCommand = Get-UvCommand

if ($uvCommand) {
    $uvVersion = & $uvCommand --version 2>&1
    Write-Host "  ✓ uv 已就绪 ($uvVersion)" -ForegroundColor Green
    
    # 配置镜像源
    Set-ChineseMirror -UvCommand $uvCommand
} else {
    Write-Host "  ✗ uv 未找到" -ForegroundColor Red
    Write-Host ""
    Write-Host "  正在自动下载 uv..." -ForegroundColor Yellow
    
    # 创建 tools 目录
    $toolsDir = Join-Path $projectRoot "tools"
    if (-not (Test-Path $toolsDir)) {
        New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
    }
    
    # 下载 uv.exe
    $uvVersion = "0.11.32"
    $downloadUrl = "https://releases.astral.sh/github/uv/releases/download/$uvVersion/uv-x86_64-pc-windows-msvc.zip"
    $zipPath = Join-Path $toolsDir "uv.zip"
    $uvExePath = Join-Path $toolsDir "uv.exe"
    
    try {
        Write-Host "    下载 uv $uvVersion..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
        
        Write-Host "    解压..." -ForegroundColor Cyan
        Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force
        
        # 删除 zip 文件
        Remove-Item $zipPath -Force
        
        if (Test-Path $uvExePath) {
            $uvCommand = $uvExePath
            $uvVersion = & $uvCommand --version 2>&1
            Write-Host "  ✓ uv 下载成功 ($uvVersion)" -ForegroundColor Green
            
            # 配置镜像源
            Set-ChineseMirror -UvCommand $uvCommand
        } else {
            Write-Host "  ✗ uv 下载失败" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "  ✗ uv 下载失败: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请手动安装 uv：" -ForegroundColor Yellow
        Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
        exit 1
    }
}

# ──────────────────────────────────────────
# [2/6] 检查/安装 Python 版本
# ──────────────────────────────────────────
Write-Host "[2/6] 检查 Python 版本 (>=3.12)..." -ForegroundColor Yellow

# 先检查系统 Python
$pythonCommand = $null
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    $versionMatch = $pythonVersion -match "(\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -ge 3 -and $minor -ge 12) {
            $pythonCommand = "python"
            Write-Host "  ✓ 系统 Python 可用 ($pythonVersion)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ 系统 Python 版本过低: $pythonVersion (需要 >= 3.12)" -ForegroundColor Yellow
        }
    }
}

# 如果系统 Python 不可用，尝试使用 uv 管理的 Python
if (-not $pythonCommand) {
    Write-Host "  尝试使用 uv 管理 Python..." -ForegroundColor Cyan
    
    # 检查 uv 是否有 Python
    $uvPythonList = & $uvCommand python list 2>&1
    $hasPython312 = $uvPythonList -match "3\.12"
    
    if ($hasPython312) {
        Write-Host "  ✓ uv 已管理 Python 3.12+" -ForegroundColor Green
        $pythonCommand = "uv run python"
    } else {
        Write-Host "  正在通过 uv 安装 Python 3.12..." -ForegroundColor Cyan
        
        # 使用 uv 安装 Python
        & $uvCommand python install 3.12 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Python 3.12 安装成功" -ForegroundColor Green
            $pythonCommand = "uv run python"
        } else {
            Write-Host "  ✗ Python 安装失败" -ForegroundColor Red
            Write-Host ""
            Write-Host "  请手动安装 Python 3.12+：" -ForegroundColor Yellow
            Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
            exit 1
        }
    }
}

# ──────────────────────────────────────────
# [3/6] 安装依赖
# ──────────────────────────────────────────
Write-Host "[3/6] 安装依赖..." -ForegroundColor Yellow

$mcpDir = Join-Path $projectRoot "run-flow-skills-mcp"

Push-Location $mcpDir
try {
    Write-Host "  正在安装依赖包（使用国内镜像）..." -ForegroundColor Cyan
    & $uvCommand sync 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

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
# [4/6] 下载 Web 静态资源（可选）
# ──────────────────────────────────────────
Write-Host "[4/6] 下载 Web 静态资源（可选）..." -ForegroundColor Yellow
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
# [5/6] 验证安装
# ──────────────────────────────────────────
Write-Host "[5/6] 验证安装..." -ForegroundColor Yellow

Push-Location $mcpDir
try {
    # 验证 MCP Server 入口点可用
    $testResult = & $uvCommand run run-flow-skills-mcp --help 2>&1
    Write-Host "  ✓ MCP Server 入口点可用" -ForegroundColor Green

    # 验证 Web 入口点可用
    $webTest = & $uvCommand run python -c "from run_flow_skills_mcp.web.app import create_app; print('OK')" 2>&1
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
# [6/6] mcp.json 路径回退方案
# ──────────────────────────────────────────
Write-Host "[6/6] 配置检查..." -ForegroundColor Yellow

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
Write-Host "下一步操作（任选一个平台）：" -ForegroundColor White
Write-Host ""
Write-Host "  Trae IDE CN：" -ForegroundColor Cyan
Write-Host "    1. 文件 → 打开文件夹 → 选择: $projectRoot" -ForegroundColor DarkGray
Write-Host "    2. 设置 → MCP → 打开'启用项目级 MCP'开关" -ForegroundColor DarkGray
Write-Host "    3. 重启 Trae" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Claude Code：" -ForegroundColor Cyan
Write-Host "    claude /open $projectRoot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Cursor / Windsurf / Continue：" -ForegroundColor Cyan
Write-Host "    打开文件夹即可（配置已入库）" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  OpenCode：" -ForegroundColor Cyan
Write-Host "    cd $projectRoot && opencode" -ForegroundColor DarkGray
Write-Host ""
  Write-Host "  WorkBuddy：" -ForegroundColor Cyan
  Write-Host "    打开文件夹即可（.workbuddy/mcp.json + .workbuddy/skills/ 已入库）" -ForegroundColor DarkGray
Write-Host ""
Write-Host "开始使用：" -ForegroundColor White
Write-Host "  /import  - 导入训练文件" -ForegroundColor DarkGray
Write-Host "  /analyze - 分析训练数据" -ForegroundColor DarkGray
Write-Host "  /plan    - 生成训练计划" -ForegroundColor DarkGray
Write-Host "  /review  - 复盘训练" -ForegroundColor DarkGray
Write-Host "  /coach   - AI 教练建议" -ForegroundColor DarkGray
Write-Host "  /stats   - 统计与导出" -ForegroundColor DarkGray
Write-Host ""
Write-Host "可选：启动 Web 可视化界面" -ForegroundColor Cyan
Write-Host "  cd run-flow-skills-mcp && uv run run-flow-skills-web" -ForegroundColor DarkGray
Write-Host "  浏览器访问 http://127.0.0.1:8002" -ForegroundColor DarkGray
Write-Host ""
Write-Host "详细部署指南：见 DEPLOY.md 和 PLATFORMS.md" -ForegroundColor Yellow
Write-Host ""
