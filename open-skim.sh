#!/bin/bash
# open-skim.sh - Skim PDF viewer wrapper
# 用于避免 displayline 的 AppleScript 参数解析问题

PDF_FILE="$1"
LINE="${2:-0}"

# 检查文件是否存在
if [[ ! -f "$PDF_FILE" ]]; then
    echo "Error: PDF file not found: $PDF_FILE" >&2
    exit 1
fi

# 使用 displayline 打开（带行号支持）
/Applications/Skim.app/Contents/SharedSupport/displayline "$LINE" "$PDF_FILE"
