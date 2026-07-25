# 下载 HTMX / Alpine.js / ECharts 到当前目录
# 用法：pwsh download_static.ps1
$ErrorActionPreference = "Stop"

$files = @{
    "htmx.min.js"   = "https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"
    "alpine.min.js" = "https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"
    "echarts.min.js" = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "下载静态资源到: $scriptDir" -ForegroundColor Cyan

foreach ($name in $files.Keys) {
    $url = $files[$name]
    $dest = Join-Path $scriptDir $name
    Write-Host "  下载 $name ..." -NoNewline
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Host " 完成 ($((Get-Item $dest).Length) bytes)" -ForegroundColor Green
    } catch {
        Write-Host " 失败: $_" -ForegroundColor Red
        Write-Host "    手动下载: $url" -ForegroundColor Yellow
    }
}

Write-Host "`n完成。如果全部成功，base.html 的 <script> 标签可正常加载。" -ForegroundColor Cyan
