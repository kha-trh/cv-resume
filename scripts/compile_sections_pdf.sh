#!/usr/bin/env bash
# ==============================================================================
# File Name: scripts/compile_sections_pdf.sh
#
# Description:
#   Compiles each generated LaTeX section file in latex/sections/*.tex as an
#   independent, standalone PDF into output/pdf/sections/<name>.pdf using
#   latexmk and latex/section_standalone.tex.
#
# How to Use:
#   Invoked automatically by build_all.sh during the PDF compilation stage, or
#   executed directly:
#       bash scripts/compile_sections_pdf.sh [cache_latex_dir]
#   Prerequisites:
#       - XeLaTeX and latexmk available in PATH (or run inside Docker)
#       - Populated latex/sections/*.tex files
#
# Where It Is Used:
#   - Called by build_all.sh to build individual section PDFs.
#   - Generates output/pdf/sections/*.pdf from latex/sections/*.tex.
# ==============================================================================

set -euo pipefail

# Always run relative to workspace root
cd "$(dirname "$0")/.."

CACHE_LATEX="${1:-.cache/latex}"
SECTIONS_CACHE="$CACHE_LATEX/sections"
OUT_DIR="output/pdf/sections"

mkdir -p "$OUT_DIR" "$SECTIONS_CACHE"

for section_file in latex/sections/*.tex; do
  name="$(basename "$section_file" .tex)"

  # Skip empty or disabled section files
  if [ ! -s "$section_file" ] || [ -z "$(grep -v '^[[:space:]]*$' "$section_file" || true)" ]; then
    rm -f "$OUT_DIR/$name.pdf" "$SECTIONS_CACHE/$name.pdf"
    continue
  fi

  latexmk -xelatex -interaction=nonstopmode -silent \
    -cd \
    -jobname="$name" \
    -output-directory="$PWD/$SECTIONS_CACHE" \
    latex/section_standalone.tex > /dev/null 2>&1

  if [ -f "$SECTIONS_CACHE/$name.pdf" ]; then
    cp "$SECTIONS_CACHE/$name.pdf" "$OUT_DIR/$name.pdf"
    echo "  wrote $OUT_DIR/$name.pdf"
  fi
done
