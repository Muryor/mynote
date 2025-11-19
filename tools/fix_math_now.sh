#!/bin/bash
cd /Users/muryor/code/mynote
python3 tools/convert_display_to_inline.py content/exams/auto/lishui_2026_nov/converted_exam.tex.bak_display_all
cp content/exams/auto/lishui_2026_nov/converted_exam.tex.bak_display_all.bak_inline content/exams/auto/lishui_2026_nov/converted_exam.tex
echo "Math conversion complete"
