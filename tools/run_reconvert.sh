#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
SCRIPT="$ROOT_DIR/word_to_tex/scripts/preprocess_docx.sh"

NJ_DOCX="$ROOT_DIR/word_to_tex/input/江苏省南京市2026届高三上学期9月学情调研数学试题.docx"
NJ_NAME="nanjing_2026_sep"
NJ_TITLE="江苏省南京市2026届高三上学期9月学情调研数学试题"

LS_DOCX="$ROOT_DIR/word_to_tex/input/浙江省丽水、湖州、衢州三地市2026届高三上学期11月教学质量检测数学试题.docx"
LS_NAME="lishui_2026_nov"
LS_TITLE="浙江省丽水、湖州、衢州三地市2026届高三上学期11月教学质量检测数学试题"

print "Running: $SCRIPT"

"$SCRIPT" "$NJ_DOCX" "$NJ_NAME" "$NJ_TITLE"
"$SCRIPT" "$LS_DOCX" "$LS_NAME" "$LS_TITLE"

echo "Done."