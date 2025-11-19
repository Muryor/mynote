#!/usr/bin/env zsh
# final_reconvert.zsh - reconvert Lishui and Nanjing with updated v1.5

cd /Users/muryor/code/mynote

echo "Reconverting Lishui..."
python3 tools/ocr_to_examx.py word_to_tex/output/lishui_2026_nov_preprocessed.md word_to_tex/output/lishui_2026_nov_examx.tex --title "丽水市 2026 年 11 月试题"
python3 tools/agent_refine.py word_to_tex/output/lishui_2026_nov_examx.tex content/exams/auto/lishui_2026_nov/converted_exam.tex --create-tikz

echo "Reconverting Nanjing..."
python3 tools/ocr_to_examx.py word_to_tex/output/nanjing_2026_sep_preprocessed.md word_to_tex/output/nanjing_2026_sep_examx.tex --title "南京市 2026 届 9 月学情调研"
python3 tools/agent_refine.py word_to_tex/output/nanjing_2026_sep_examx.tex content/exams/auto/nanjing_2026_sep/converted_exam.tex --create-tikz

echo "Done reconversion."
