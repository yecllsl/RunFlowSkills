# Plan 5 实施报告：CI/CD + 分发脚本 + 安装脚本

> **状态**: DONE_WITH_CONCERNS
> **执行日期**: 2026-07-25
> **测试摘要**: 336 passed, 5 failed（5 个全部因 `.trae/mcp.json` 缺失，与 Plan 4 同一根因）

---

## 一、执行总览

| Task | 状态 | 测试数 | Commit |
|------|------|--------|--------|
| Task 1: install.ps1 + install.sh | ✅ 完成 | 6 通过 | 6de12e1 |
| Task 2: build-release.ps1 + build-release.sh | ✅ 完成 | 9 通过（含 3 评审修正点） | afcffaf |
| Task 3: .github/workflows/test.yml | ✅ 完成 | 5 通过（release 相关 1 个待 Task 4） | ecb9786 |
| Task 4: .github/workflows/release.yml | ✅ 完成 | 5 通过（追加） | d5644b7 |
| Task 5: 全量测试 + 冒烟验证 + test_release_readiness.py | ✅ 完成 | 22 通过 / 1 失败（mcp.json） | f51c934 |

**总计**: 5 commits + 1 个 concern（mcp.json 沿用 Plan 4 已知问题）

---

## 二、关键产出

### 1. 文件清单

```
RunFlowSkills/
├── install.ps1                                    ✅ Windows 安装脚本
├── install.sh                                     ✅ Linux/macOS 安装脚本
├── .gitignore                                     ✅ 根目录忽略规则（新增）
├── scripts/
│   ├── build-release.ps1                          ✅ Windows 发布包构建
│   └── build-release.sh                           ✅ Linux/macOS 发布包构建
└── .github/workflows/
    ├── test.yml                                   ✅ CI：单元 + E2E 测试
    └── release.yml                                ✅ CD：自动 GitHub Release

run-flow-skills-mcp/tests/
├── test_install_scripts.py                        ✅ 6 tests
├── test_build_scripts.py                          ✅ 9 tests
├── test_workflows.py                              ✅ 11 tests
└── test_release_readiness.py                      ✅ 23 tests（1 失败：mcp.json）
```

### 2. 测试统计

- **Plan 5 新增测试**: 49 个
  - test_install_scripts.py: 6 ✅
  - test_build_scripts.py: 9 ✅（含 3 个评审修正点验证）
  - test_workflows.py: 11 ✅
  - test_release_readiness.py: 23（22 ✅ + 1 ❌ mcp.json）
- **全量测试**: 336 passed, 5 failed
- **失败原因**: 5 个全部因 `.trae/mcp.json` 缺失
  - 4 个来自 test_mcp_config.py（Plan 4 已知问题）
  - 1 个来自 test_release_readiness.py::test_mcp_json_exists（同根因）

### 3. 冒烟验证结果

#### PowerShell 构建脚本 (`build-release.ps1`)

```
[1/6] Clean previous build...           ✅
[2/6] Create directory structure...     ✅
[3/6] Copy .trae config...              ✅
[4/6] Copy run-flow-skills-mcp source.. ✅
[5/6] Copy docs and install scripts...  ✅
[6/6] Verify and pack...                ✅ verified (92 files, no .venv)
  Packing zip...                        ✅ RunFlowSkills-v0.1.0.zip (0.21 MB)
  Packing tar.gz...                     ✅ RunFlowSkills-v0.1.0.tar.gz (0.17 MB)
```

#### 发布包内容验证

- 顶层：`.trae/`, `run-flow-skills-mcp/`, `scripts/`, 4 文档, install.ps1/sh
- `.trae/mcp.json`: 使用 `${workspaceFolder}` 变量 ✅
- `data/` 下只有 `.gitkeep`，无用户数据 ✅
- 无 `.venv`、无 `dist/` 嵌套 ✅

#### 脚本语法验证

| 脚本 | 检查方式 | 结果 |
|------|---------|------|
| install.sh | `bash -n` | ✅ OK |
| build-release.sh | `bash -n` | ✅ OK |
| install.ps1 | PSParser tokenization | ✅ OK |
| build-release.ps1 | PSParser tokenization | ✅ OK |

---

## 三、关键关注点

### ⚠️ Concern 1: `.trae/mcp.json` 沿用 Plan 4 已知问题

**问题**: 5 个测试失败，全部因 `.trae/mcp.json` 文件不存在。
- 4 个来自 `test_mcp_config.py`（Plan 4 遗留）
- 1 个来自 `test_release_readiness.py::test_mcp_json_exists`（Plan 5 新增）

**根因**: 系统安全策略将 `.trae/mcp.json` 列入黑名单，禁止 AI 创建（详见 plan4-report.md）。

**用户需手动操作**: 在 `D:\yecll\Documents\LocalCode\RunFlowSkills\.trae\mcp.json` 创建文件，内容如下（与 build-release 脚本生成的发布版一致）：

```json
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
```

创建后运行 `uv run pytest tests/ -v`，预期 341 passed。

### ✅ 评审修正点已落实

build-release.ps1 和 build-release.sh 均包含 3 项评审要求的验证：

1. **`.venv` 未误包含验证**:
   - PowerShell: `if (Test-Path (Join-Path $mcpDst ".venv")) { ... exit 1 }`
   - Bash: `if [ -d "$STAGING_DIR/run-flow-skills-mcp/.venv" ]; then ... exit 1; fi`

2. **`data/` 下只有 `.gitkeep` 验证**:
   - PowerShell: `Get-ChildItem ... | Where-Object { $_.Name -ne ".gitkeep" }`，有则 exit 1
   - Bash: `find ... -type f ! -name '.gitkeep'`，有则 exit 1

3. **`dist/` 未误包含验证**:
   - PowerShell: `if (Test-Path (Join-Path $stagingDir "dist")) { ... exit 1 }`
   - Bash: `if [ -d "$STAGING_DIR/dist" ]; then ... exit 1; fi`

通过 `test_build_scripts.py` 中 3 个专门测试用例验证（test_build_scripts_verify_no_venv_included / test_build_scripts_verify_no_user_data_in_data_dir / test_build_scripts_verify_no_dist_included），全部 PASS。

### ✅ Bug 修复：build-release.ps1 路径计算错误

**问题**: 原始脚本 `$projectRoot = $PSScriptRoot | Split-Path | Split-Path` 调用了两次 `Split-Path`，从 `scripts/` 目录上溯两级到 `LocalCode/`，导致 `dist/` 被创建到 `D:\yecll\Documents\LocalCode\dist\` 而非 `D:\yecll\Documents\LocalCode\RunFlowSkills\dist\`。bash 版本使用 `$SCRIPT_DIR/..` 上溯一级是正确的。

**修复**: 改为 `$projectRoot = $PSScriptRoot | Split-Path`（上溯一级到 `RunFlowSkills/`）。

**验证**: 修复后 `pwsh .\scripts\build-release.ps1 -Version 0.1.0` 成功生成 `dist/RunFlowSkills-v0.1.0.zip` 和 `dist/RunFlowSkills-v0.1.0.tar.gz`。

### ✅ 三种分发格式支持

| 格式 | PowerShell 脚本 | Bash 脚本 | 说明 |
|------|----------------|-----------|------|
| `.zip` | Compress-Archive（原生） | zip 命令 | Windows 主推 |
| `.tar.zst` | ⚠️ 不支持（注释说明） | zstd 命令 | 现代 Linux/macOS 推荐 |
| `.tar.gz` | tar 命令（Win10+ 内置） | tar 命令 | 兼容 fallback |

PowerShell 脚本不支持 tar.zst（Windows 无原生 zstd），在脚本注释和输出中明确说明需手动用 7zip/zstd。Bash 脚本支持全部 3 种格式。release.yml CI 在 Ubuntu 上运行，使用 bash 脚本，三种格式全部生成。

---

## 四、TDD 循环验证

每个 Task 严格遵循 TDD：

| Task | RED 阶段 | GREEN 阶段 |
|------|---------|-----------|
| Task 1 | 6 failed（脚本不存在） | 6 passed |
| Task 2 | 9 failed（脚本不存在） | 9 passed |
| Task 3 | 6 failed（test.yml 不存在） | 5 passed, 1 failed（release.yml 待 Task 4） |
| Task 4 | 5 failed（release.yml 不存在） | 5 passed（追加到 11 全通过） |
| Task 5 | 3 failed（mcp.json + .gitignore） | 1 failed（mcp.json 系统限制） + 22 passed |

---

## 五、Spec 覆盖检查

| 设计文档章节 | 覆盖 Task | 状态 |
|---|---|---|
| 13.1 GitHub Actions test.yml | Task 3 | ✅ Python 3.12/3.13 矩阵 + E2E 仅 push 时跑 |
| 13.1 GitHub Actions release.yml | Task 4 | ✅ push tag v*.*.* 触发 + workflow_dispatch 手动 |
| 13.2 分发格式 zip/tar.zst/tar.gz | Task 2 | ✅ 三种格式（PS 不支持 zst，bash 全支持） |
| 13.3 安装脚本 | Task 1 | ✅ install.ps1/install.sh + Trae 打开提示 |

---

## 六、CI/CD 流程说明

### test.yml（CI）

- **触发**: push 到 main/develop + PR 到 main
- **unit-tests job**: Python 3.12/3.13 矩阵，ruff lint + mypy + pytest（排除 e2e）
- **e2e-tests job**: 仅 push 时触发（`if: github.event_name == 'push'`），需要 unit-tests 通过后运行，安装 Playwright Chromium 跑 E2E
- **覆盖率上传**: codecov（仅 Python 3.12 矩阵）

### release.yml（CD）

- **触发**: push tag `v*.*.*`（如 `v0.1.0`）+ workflow_dispatch 手动
- **构建**: 调用 `bash scripts/build-release.sh "$VERSION"` 生成三种格式
- **验证**: 检查 dist/ 下三个文件都存在
- **资产删除**: 允许重新上传（先删除已存在的同名资产）
- **发布**: softprops/action-gh-release@v2 创建 GitHub Release + 自动生成 release notes

---

## 七、后续行动项

1. **【高优先级】用户手动创建 `.trae/mcp.json`**（参见上方 JSON 内容）
   - 创建后预期 341 passed, 0 failed
2. **【可选】创建 v0.1.0 tag 触发首次发布**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
   这会触发 release.yml 自动构建并上传 GitHub Release
3. **【可选】Windows 用户如需 tar.zst 格式**: 手动安装 zstd 后运行 bash 脚本

---

## 八、结论

Plan 5 核心交付物全部完成：
- **安装脚本** (install.ps1/install.sh)：5 步向导式安装，提示 Trae IDE 使用方式
- **构建脚本** (build-release.ps1/build-release.sh)：白名单复制 + 3 项安全验证 + 三种格式打包
- **CI** (test.yml)：Python 3.12/3.13 矩阵 + 单元/集成/E2E 分层测试
- **CD** (release.yml)：tag 触发自动构建 + GitHub Release 发布

**唯一阻塞项**：`.trae/mcp.json` 受系统黑名单保护需用户手动创建（Plan 4 已知问题），创建后全部 341 个测试通过。

**状态**: DONE_WITH_CONCERNS
**测试摘要**: 336 passed, 5 failed（mcp.json 相关，待用户手动创建文件后通过）
