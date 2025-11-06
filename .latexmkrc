# Force XeLaTeX for all PDF builds (unless overridden by env)
$pdflatex = 'xelatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 %O %S';
$latex    = $pdflatex;
$xelatex  = $pdflatex;

$pdf_mode   = 1;      # direct pdf
$silent     = 1;      # quieter logs
$bibtex_use = 2;      # biber if present, else bibtex

# Output and aux directory management
$out_dir = 'output/.aux';
$aux_dir = 'output/.aux';

# Comprehensive cleanup extensions
$clean_ext = 'acn acr alg aux bbl bcf blg dvi fdb_latexmk fls glg glo gls '
           . 'idx ilg ind ist lof log lot nav out run.xml snm synctex.gz toc '
           . 'xdv thm thm~ auxlock bc* *-blx.bib *-converted-to.pdf';
$cleanup_includes_generated = 1;

# Optional: set USE_LUALATEX=1 to switch to LuaLaTeX without editing this file
if (exists $ENV{USE_LUALATEX} && $ENV{USE_LUALATEX} eq '1') {
  $pdflatex = 'lualatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 %O %S';
  $latex    = $pdflatex;
}
