<#
.SYNOPSIS
    按目标 agent 平台生成对应的 MCP 配置文件。

.DESCRIPTION
    不同 agent 平台的 MCP 配置位置与变量约定存在差异：
      - Trae       : .trae/mcp.json     使用 ${workspaceFolder} 变量
      - Claude Code: .mcp.json          使用绝对路径或 $CLAUDE_PROJECT_DIR
      - Cursor     : .cursor/mcp.json  使用绝对路径
      - Windsurf   : mcp_config.json    使用绝对路径
      - Continue   : .continue/config.json  使用绝对路径
      - OpenCode   : opencode.json      使用绝对路径，MCP 结构为 {type,command[],enabled}
      - WorkBuddy  : .workbuddy/mcp.json  使用绝对路径

    本脚本根据目标平台生成对应配置，避免手工维护多份配置导致漂移。

.PARAMETER Platform
    单个目标平台名称（必填）：trae / claude-code / cursor / windsurf / continue / opencode / workbuddy

.PARAMETER OutputPath
    输出文件路径（可选，默认按平台标准位置）

.PARAMETER PythonRunner
    MCP 启动方式：uv（默认）/ python。
    - uv     : 使用 `uv run --directory <dir> run-flow-skills-mcp`
    - python : 使用 `python -m run_flow_skills_mcp.server`（需先 pip install）

.EXAMPLE
    .\scripts\generate-mcp-config.ps1 -Platform claude-code
    生成 .mcp.json（Claude Code 标准位置）

.EXAMPLE
    .\scripts\generate-mcp-config.ps1 -Platform cursor -PythonRunner python
    生成 .cursor/mcp.json，使用 python 启动方式

.NOTES
    本脚本不依赖 sync-platforms.ps1，可独立调用。
    生成后请用户在对应平台"启用 MCP"。
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('trae', 'claude-code', 'cursor', 'windsurf', 'continue', 'opencode', 'workbuddy')]
    [string]$Platform,

    [string]$OutputPath,

    [ValidateSet('uv', 'python')]
    [string]$PythonRunner = 'uv'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$McpDir = Join-Path $ProjectRoot 'run-flow-skills-mcp'

Write-Host "=== MCP 配置生成器 ===" -ForegroundColor Cyan
Write-Host "目标平台: $Platform"
Write-Host "启动方式: $PythonRunner"
Write-Host ""

# 按平台与启动方式构造命令
function Get-McpCommand {
    param([string]$Runner, [string]$Platform)

    if ($Runner -eq 'uv') {
        # uv 启动：根据平台选择变量占位符
        $dirVar = switch ($Platform) {
            'trae'        { '${workspaceFolder}/run-flow-skills-mcp' }
            'claude-code' { "$ProjectRoot/run-flow-skills-mcp" }
            'cursor'      { "$ProjectRoot/run-flow-skills-mcp" }
            'windsurf'    { "$ProjectRoot/run-flow-skills-mcp" }
            'continue'    { "$ProjectRoot/run-flow-skills-mcp" }
            'opencode'    { "$ProjectRoot/run-flow-skills-mcp" }  # OpenCode 不支持 ${workspaceFolder}
            'workbuddy'   { "$ProjectRoot/run-flow-skills-mcp" }
        }
        return @{
            command = 'uv'
            args    = @('run', '--directory', $dirVar, 'run-flow-skills-mcp')
        }
    }
    else {
        # python 启动：要求用户已 pip install -e ./run-flow-skills-mcp
        return @{
            command = 'python'
            args    = @('-m', 'run_flow_skills_mcp.server')
            env     = @{
                PYTHONPATH = $McpDir
            }
        }
    }
}

# 按平台确定输出路径
function Get-OutputPath {
    param([string]$Platform, [string]$Override)

    if ($Override) { return $Override }
    switch ($Platform) {
        'trae'        { return (Join-Path $ProjectRoot '.trae\mcp.json') }
        'claude-code' { return (Join-Path $ProjectRoot '.mcp.json') }
        'cursor'      { return (Join-Path $ProjectRoot '.cursor\mcp.json') }
        'windsurf'    { return (Join-Path $ProjectRoot '.windsurf\mcp.json') }
        'continue'    { return (Join-Path $ProjectRoot '.continue\mcpServers\run-flow-skills-mcp.yaml') }
        'opencode'    { return (Join-Path $ProjectRoot 'opencode.json') }
        'workbuddy'   { return (Join-Path $ProjectRoot '.workbuddy\mcp.json') }
    }
}

# 构造配置对象
$cmd = Get-McpCommand -Runner $PythonRunner -Platform $Platform

# 按平台构造不同的配置结构
$isYaml = $false
switch ($Platform) {
    'continue' {
        # Continue: 现代格式 .continue/mcpServers/ 目录下的 YAML 文件
        $config = @"
name: run-flow-skills-mcp
command: $($cmd.command)
args:
$($cmd.args | ForEach-Object { "  - $_" } | Out-String)
"@
        $isYaml = $true
    }
    'windsurf' {
        # Windsurf: 现代格式 .windsurf/mcp.json（标准 mcpServers 结构）
        $config = @{
            mcpServers = @{
                'run-flow-skills-mcp' = $cmd
            }
        }
    }
    'opencode' {
        # OpenCode: 专用结构 {type: local, command: [...], enabled: true}
        $opencodeMcp = @{
            type    = 'local'
            command = @($cmd.command) + $cmd.args
            enabled = $true
        }
        $config = @{
            '$schema'    = 'https://opencode.ai/config.json'
            mcp          = @{ 'run-flow-skills-mcp' = $opencodeMcp }
            instructions = @('AGENTS.md')
        }
    }
    default {
        # Trae / Claude Code / Cursor / WorkBuddy: 标准 mcpServers 结构
        $config = @{
            mcpServers = @{
                'run-flow-skills-mcp' = $cmd
            }
        }
    }
}

# 序列化为 JSON 或直接使用 YAML 字符串
if ($isYaml) {
    $output = $config
} else {
    $output = $config | ConvertTo-Json -Depth 10
}

# 确定输出路径并写入
$outPath = Get-OutputPath -Platform $Platform -Override $OutputPath
$parent = Split-Path -Parent $outPath
if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
Set-Content -Path $outPath -Value $output -Encoding UTF8 -NoNewline

Write-Host "[OK] 已生成: $outPath" -ForegroundColor Green
Write-Host ""
Write-Host "配置内容预览:" -ForegroundColor Cyan
Write-Host $json
Write-Host ""
Write-Host "下一步: 在 $Platform 平台启用 MCP 服务（通常需重启宿主）" -ForegroundColor Yellow
