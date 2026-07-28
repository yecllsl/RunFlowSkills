<#
.SYNOPSIS
    将根目录 AGENTS.md + .trae/skills/ 单一事实源同步到各 agent 平台目录。

.DESCRIPTION
    本脚本不改变单一事实源，只在目标平台目录生成镜像副本，确保跨平台兼容。
    当前已支持：trae（默认源，不操作）、claude-code、cursor、windsurf、continue、opencode、workbuddy。

    单一事实源：
      - 根目录 AGENTS.md        （规则统一入口）
      - .trae/skills/<name>/SKILL.md  （6 个 Skill 定义）

    目标平台镜像规则：
      - claude-code : .claude/skills/<name>/SKILL.md + CLAUDE.md（复制 AGENTS.md）
      - cursor     : .cursor/rules/runflow-agents.mdc + .cursor/rules/<skill>.mdc
      - windsurf   : .windsurf/rules/runflow-skills.md（Skills 指南） + .windsurfrules（兼容 fallback）；约束规则通过 AGENTS.md 直接读取
      - continue   : .continue/config.yaml（skills 索引 + MCP） + .continue/mcpServers/*.yaml + config.json（兼容 fallback）；约束规则通过 AGENTS.md 直接读取
      - opencode   : opencode.json（OpenCode 专用 MCP 结构） + .opencode/skills/
      - workbuddy  : .workbuddy/mcp.json + .workbuddy/skills/（原生 Skill 支持）

.PARAMETER Platforms
    要同步的平台列表，默认全部：trae,claude-code,cursor,windsurf,continue,opencode,workbuddy
    trae 为源平台，传入时仅做校验不写文件。

.PARAMETER DryRun
    仅打印将要执行的操作，不实际写文件。

.EXAMPLE
    .\scripts\sync-platforms.ps1
    同步全部平台

.EXAMPLE
    .\scripts\sync-platforms.ps1 -Platforms claude-code,cursor -DryRun
    预演 claude-code 与 cursor 同步过程

.NOTES
    本脚本遵循"单一事实源 + 生成器"模式，禁止手动编辑目标平台镜像目录。
    镜像目录入库（不加入 .gitignore），便于用户开箱即用。
    开发者修改源后需重新运行本脚本并提交镜像变更。
#>

[CmdletBinding()]
param(
    [string[]]$Platforms = @('trae', 'claude-code', 'cursor', 'windsurf', 'continue', 'opencode', 'workbuddy'),
    [switch]$DryRun
)

# 项目根目录（脚本位于 scripts/ 下，向上一级即根目录）
$ErrorActionPreference = 'Stop'
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $ProjectRoot

Write-Host "=== RunFlowSkills 平台同步脚本 ===" -ForegroundColor Cyan
Write-Host "项目根目录: $ProjectRoot"
Write-Host "目标平台: $($Platforms -join ', ')"
Write-Host "DryRun: $DryRun"
Write-Host ""

# 校验单一事实源是否存在
$agentsMd = Join-Path $ProjectRoot 'AGENTS.md'
$sourceSkillsDir = Join-Path $ProjectRoot '.trae\skills'

if (-not (Test-Path $agentsMd)) {
    throw "单一事实源缺失: $agentsMd"
}
if (-not (Test-Path $sourceSkillsDir)) {
    throw "单一事实源缺失: $sourceSkillsDir"
}

# 读取 AGENTS.md 内容（多次复用）
$agentsContent = Get-Content -Path $agentsMd -Raw -Encoding UTF8

# 收集所有 Skill 定义
$skills = Get-ChildItem -Path $sourceSkillsDir -Directory | Sort-Object Name
Write-Host "发现 $($skills.Count) 个源 Skill: $($skills.Name -join ', ')"
Write-Host ""

# 同步辅助函数：写文件（支持 DryRun）
function Write-PlatformFile {
    param(
        [string]$Path,
        [string]$Content,
        [switch]$DryRun
    )
    if ($DryRun) {
        Write-Host "  [DRY] 将写入: $Path ($($Content.Length) chars)" -ForegroundColor Yellow
        return
    }
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Set-Content -Path $Path -Value $Content -Encoding UTF8 -NoNewline
    Write-Host "  [OK] 已写入: $Path" -ForegroundColor Green
}

# 同步辅助函数：复制目录（支持 DryRun）
function Copy-PlatformDir {
    param(
        [string]$Source,
        [string]$Destination,
        [switch]$DryRun
    )
    if ($DryRun) {
        Write-Host "  [DRY] 将镜像: $Source -> $Destination" -ForegroundColor Yellow
        return
    }
    if (Test-Path $Destination) {
        Remove-Item -Path $Destination -Recurse -Force
    }
    Copy-Item -Path $Source -Destination $Destination -Recurse -Force
    Write-Host "  [OK] 已镜像: $Destination" -ForegroundColor Green
}

# === 平台同步实现 ===

function Sync-Trae {
    param([switch]$DryRun)
    Write-Host "[Trae] 作为源平台，仅校验存在性..." -ForegroundColor Cyan
    if (Test-Path $sourceSkillsDir) {
        Write-Host "  [OK] .trae/skills/ 存在 ($($skills.Count) 个 Skill)" -ForegroundColor Green
    } else {
        throw "  .trae/skills/ 不存在"
    }
    if (Test-Path (Join-Path $ProjectRoot '.trae\mcp.json')) {
        Write-Host "  [OK] .trae/mcp.json 存在" -ForegroundColor Green
    }
}

function Sync-ClaudeCode {
    param([switch]$DryRun)
    Write-Host "[Claude Code] 同步到 .claude/ ..." -ForegroundColor Cyan
    # 1. 复制 AGENTS.md 到 CLAUDE.md（Anthropic 标准）
    Write-PlatformFile -Path (Join-Path $ProjectRoot 'CLAUDE.md') -Content $agentsContent -DryRun:$DryRun
    # 2. 复制 skills 目录到 .claude/skills/
    Copy-PlatformDir -Source $sourceSkillsDir -Destination (Join-Path $ProjectRoot '.claude\skills') -DryRun:$DryRun
    # 3. 生成 .mcp.json（Claude Code 标准位置）
    $mcpConfig = @{
        mcpServers = @{
            'run-flow-skills-mcp' = @{
                command = 'uv'
                args    = @('run', '--directory', "$ProjectRoot/run-flow-skills-mcp", 'run-flow-skills-mcp')
            }
        }
    } | ConvertTo-Json -Depth 10
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.mcp.json') -Content $mcpConfig -DryRun:$DryRun
}

function Sync-Cursor {
    param([switch]$DryRun)
    Write-Host "[Cursor] 同步到 .cursor/ ..." -ForegroundColor Cyan
    # 1. 生成 .cursor/rules/runflow-agents.mdc（Cursor 标准 rule 格式）
    $cursorRule = @"
---
description: RunFlowSkills 跨平台 Agent 规范
globs: "**/*"
alwaysApply: true
---

$agentsContent
"@
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.cursor\rules\runflow-agents.mdc') -Content $cursorRule -DryRun:$DryRun
    # 2. 为每个 Skill 生成 .mdc 文件
    foreach ($skill in $skills) {
        $skillMd = Join-Path $skill.FullName 'SKILL.md'
        if (-not (Test-Path $skillMd)) { continue }
        $skillContent = Get-Content -Path $skillMd -Raw -Encoding UTF8
        $skillName = $skill.Name
        $mdc = @"
---
description: $skillName Skill
globs: "**/*"
alwaysApply: false
---

$skillContent
"@
        Write-PlatformFile -Path (Join-Path $ProjectRoot ".cursor\rules\$skillName.mdc") -Content $mdc -DryRun:$DryRun
    }
    # 3. 生成 .cursor/mcp.json
    $mcpConfig = @{
        mcpServers = @{
            'run-flow-skills-mcp' = @{
                command = 'uv'
                args    = @('run', '--directory', "$ProjectRoot/run-flow-skills-mcp", 'run-flow-skills-mcp')
            }
        }
    } | ConvertTo-Json -Depth 10
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.cursor\mcp.json') -Content $mcpConfig -DryRun:$DryRun
}

function Sync-Windsurf {
    param([switch]$DryRun)
    Write-Host "[Windsurf] 同步到 .windsurf/rules/ + .windsurfrules（兼容）..." -ForegroundColor Cyan
    # Windsurf 原生读取 AGENTS.md 作为约束规则（单一事实源）
    # .windsurf/rules/ 仅用于 Skills 使用指南（非约束规则）

    # 1. Skills 使用指南（.windsurf/rules/ 目录，model_decision 触发）
    $windsurfRulesDir = Join-Path $ProjectRoot '.windsurf\rules'
    $skillsList = ($skills | ForEach-Object { "- `/$($_.Name)`: $($_.Name)" }) -join "`n"
    $skillsGuide = @"
---
trigger: model_decision
description: "用户询问跑步训练、导入数据、分析负荷、制定计划、复盘训练、教练建议、统计分布时使用"
---

# RunFlowSkills 技能清单

本项目提供 6 个跑步数据分析技能，通过 MCP Tool 暴露：

$skillsList

## 使用方式

直接用自然语言描述需求，AI 会自动匹配对应技能：
- "导入今天的跑步文件" → runflow-import
- "分析最近 30 天的训练" → runflow-analyze
- "帮我制定全马破 4 的 12 周计划" → runflow-plan
- "复盘本周训练" → runflow-review
- "今天能跑间歇吗？" → runflow-coach
- "按周统计跑量" → runflow-stats
"@
    Write-PlatformFile -Path (Join-Path $windsurfRulesDir 'runflow-skills.md') -Content $skillsGuide -DryRun:$DryRun

    # 2. 兼容格式：.windsurfrules（Windsurf 仍读取，作为 fallback）
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.windsurfrules') -Content $agentsContent -DryRun:$DryRun
}

function Sync-Continue {
    param([switch]$DryRun)
    Write-Host "[Continue] 同步到 config.yaml + .continue/mcpServers/ ..." -ForegroundColor Cyan
    # Continue 原生读取 AGENTS.md 作为约束规则（单一事实源）
    # config.yaml 仅配置 skills 索引和 MCP 服务器

    # 1. 生成 config.yaml（YAML 格式，现代 Continue 标准）
    $skillsYamlLines = @()
    foreach ($skill in $skills) {
        $skillsYamlLines += "  - path: .trae/skills/$($skill.Name)/SKILL.md"
        $skillsYamlLines += "    name: $($skill.Name)"
    }
    $skillsYaml = $skillsYamlLines -join "`n"

    $configYaml = @"
name: RunFlowSkills
version: 1.0.0
schema: v1
skills:
$skillsYaml
mcpServers:
  - name: run-flow-skills-mcp
    command: uv
    args:
      - run
      - --directory
      - $ProjectRoot/run-flow-skills-mcp
      - run-flow-skills-mcp
"@
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.continue\config.yaml') -Content $configYaml -DryRun:$DryRun

    # 2. 生成 MCP 独立配置文件（.continue/mcpServers/ 目录）
    $mcpServerYaml = @"
name: run-flow-skills-mcp
command: uv
args:
  - run
  - --directory
  - $ProjectRoot/run-flow-skills-mcp
  - run-flow-skills-mcp
"@
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.continue\mcpServers\run-flow-skills-mcp.yaml') -Content $mcpServerYaml -DryRun:$DryRun

    # 3. 保留 config.json 作为兼容 fallback（Continue 仍读取但已废弃）
    $configJson = @{
        rules = @(
            @{ name = 'runflow-agents'; path = 'AGENTS.md' }
        )
        skills = $skills | ForEach-Object {
            @{ name = $_.Name; path = ".trae/skills/$($_.Name)/SKILL.md" }
        }
        mcp = @{
            servers = @{
                'run-flow-skills-mcp' = @{
                    command = 'uv'
                    args    = @('run', '--directory', "$ProjectRoot/run-flow-skills-mcp", 'run-flow-skills-mcp')
                }
            }
        }
    } | ConvertTo-Json -Depth 10
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.continue\config.json') -Content $configJson -DryRun:$DryRun
}

function Sync-OpenCode {
    param([switch]$DryRun)
    Write-Host "[OpenCode] 同步到 opencode.json + .opencode/skills/ ..." -ForegroundColor Cyan
    # 1. 生成 opencode.json（OpenCode 专用 MCP 结构：type=local, command[], enabled）
    # OpenCode 不支持 ${workspaceFolder}，必须使用绝对路径
    $opencodeConfig = @{
        '$schema' = 'https://opencode.ai/config.json'
        mcp       = @{
            'run-flow-skills-mcp' = @{
                type    = 'local'
                command = @('uv', 'run', '--directory', "$ProjectRoot/run-flow-skills-mcp", 'run-flow-skills-mcp')
                enabled = $true
            }
        }
        # 引用 AGENTS.md 作为指令（OpenCode 会自动读取，此处显式声明便于审计）
        instructions = @('AGENTS.md')
    } | ConvertTo-Json -Depth 10
    Write-PlatformFile -Path (Join-Path $ProjectRoot 'opencode.json') -Content $opencodeConfig -DryRun:$DryRun
    # 2. 镜像 skills 目录到 .opencode/skills/
    Copy-PlatformDir -Source $sourceSkillsDir -Destination (Join-Path $ProjectRoot '.opencode\skills') -DryRun:$DryRun
}

function Sync-WorkBuddy {
    param([switch]$DryRun)
    Write-Host "[WorkBuddy] 同步到 .workbuddy/ ..." -ForegroundColor Cyan
    # 1. 镜像 skills 目录到 .workbuddy/skills/（WorkBuddy 原生 Skill 支持）
    Copy-PlatformDir -Source $sourceSkillsDir -Destination (Join-Path $ProjectRoot '.workbuddy\skills') -DryRun:$DryRun
    # 2. 生成 .workbuddy/mcp.json
    $workbuddyConfig = @{
        mcpServers = @{
            'run-flow-skills-mcp' = @{
                command = 'uv'
                args    = @('run', '--directory', "$ProjectRoot/run-flow-skills-mcp", 'run-flow-skills-mcp')
            }
        }
    } | ConvertTo-Json -Depth 10
    Write-PlatformFile -Path (Join-Path $ProjectRoot '.workbuddy\mcp.json') -Content $workbuddyConfig -DryRun:$DryRun
}

# === 执行同步 ===
foreach ($platform in $Platforms) {
    Write-Host ""
    switch ($platform) {
        'trae'        { Sync-Trae -DryRun:$DryRun }
        'claude-code' { Sync-ClaudeCode -DryRun:$DryRun }
        'cursor'      { Sync-Cursor -DryRun:$DryRun }
        'windsurf'    { Sync-Windsurf -DryRun:$DryRun }
        'continue'    { Sync-Continue -DryRun:$DryRun }
        'opencode'    { Sync-OpenCode -DryRun:$DryRun }
        'workbuddy'   { Sync-WorkBuddy -DryRun:$DryRun }
        default       { Write-Warning "未知平台: $platform（跳过）" }
    }
}

Write-Host ""
Write-Host "=== 同步完成 ===" -ForegroundColor Cyan
Write-Host "提示: 镜像目录（.claude/、.cursor/、.windsurf/、.continue/（含 config.yaml + mcpServers/ + rules/）、.opencode/、.workbuddy/、opencode.json、CLAUDE.md、.mcp.json）入库以便开箱即用。" -ForegroundColor Green
Write-Host "开发者修改源（AGENTS.md / .trae/skills/）后，请重新运行本脚本并提交镜像变更。" -ForegroundColor Yellow
