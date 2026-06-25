#!/usr/bin/env bash
# compile_sections_pdf.sh
# Compiles every latex/sections/*.tex as a standalone PDF into output/pdf/sections/.
# Called by build_all.sh inside the Docker container (or Dev Container).
#
# Usage: bash scripts/compile_sections_pdf.sh [cache_latex_dir]
#   cache_latex_dir defaults to .cache/latex

set -euo pipefail

# Always run relative to workspace root
cd "$(dirname "$0")/.."

CACHE_LATEX="${1:-.cache/latex}"
SECTIONS_CACHE="$CACHE_LATEX/sections"
OUT_DIR="output/pdf/sections"

mkdir -p "$OUT_DIR" "$SECTIONS_CACHE"

for section_file in latex/sections/*.tex; do
  name="$(basename "$section_file" .tex)"

  latexmk -xelatex -interaction=nonstopmode -silent \
    -cd \
    -jobname="$name" \
    -output-directory="$PWD/$SECTIONS_CACHE" \
    latex/section_standalone.tex > /dev/null 2>&1

  cp "$SECTIONS_CACHE/$name.pdf" "$OUT_DIR/$name.pdf"
  echo "  wrote $OUT_DIR/$name.pdf"
done
