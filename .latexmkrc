# Force XeLaTeX for all PDF builds (unless overridden by env)
$pdflatex = 'xelatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 %O %S';
$latex    = $pdflatex;
$xelatex  = $pdflatex;

$pdf_mode   = 1;      # direct pdf
$silent     = 1;      # quieter logs
$bibtex_use = 2;      # biber if present, else bibtex

# Optional: set USE_LUALATEX=1 to switch to LuaLaTeX without editing this file
if (exists $ENV{USE_LUALATEX} && $ENV{USE_LUALATEX} eq '1') {
  $pdflatex = 'lualatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 %O %S';
  $latex    = $pdflatex;
}
