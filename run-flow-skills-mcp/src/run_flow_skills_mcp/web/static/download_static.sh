#!/usr/bin/env bash
# 下载 HTMX / Alpine.js / ECharts 到当前目录
# 用法：bash download_static.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

declare -A FILES=(
    ["htmx.min.js"]="https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"
    ["alpine.min.js"]="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"
    ["echarts.min.js"]="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
)

echo "下载静态资源到: $SCRIPT_DIR"

for name in "${!FILES[@]}"; do
    url="${FILES[$name]}"
    echo -n "  下载 $name ..."
    if curl -sSL -o "$name" "$url"; then
        size=$(wc -c < "$name")
        echo " 完成 (${size} bytes)"
    else
        echo " 失败"
        echo "    手动下载: $url"
    fi
done

echo ""
echo "完成。如果全部成功，base.html 的 <script> 标签可正常加载。"
