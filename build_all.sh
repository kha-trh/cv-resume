#!/usr/bin/env bash
# build_all.sh — Single entry point for all resume build operations.
# Usage: ./build_all.sh [--tex] [--html] [--pdf] [--all] [--clean] [--force]
set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────
IMAGE="resume-builder"
CACHE_DIR=".cache"
CACHE_FONTCONFIG="$CACHE_DIR/fontconfig"
CACHE_LATEX="$CACHE_DIR/latex"
CACHE_DATA_HASH="$CACHE_DIR/data.sha256"
CACHE_IMAGE_HASH="$CACHE_DIR/image.sha256"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ── Helpers ────────────────────────────────────────────────────────────────────
header()  { echo -e "\n${CYAN}── $1 ──────────────────────────────────────────────────────────${NC}"; }
success() { echo -e "${GREEN}✔  $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠  $1${NC}"; }
error()   { echo -e "${RED}✘  $1${NC}" >&2; exit 1; }

# ── Argument parsing ───────────────────────────────────────────────────────────
DO_TEX=false; DO_HTML=false; DO_PDF=false; DO_CLEAN=false; DO_FORCE=false
EXPLICIT_STAGE=false

for arg in "$@"; do
  case "$arg" in
    --tex)   DO_TEX=true;  EXPLICIT_STAGE=true ;;
    --html)  DO_HTML=true; EXPLICIT_STAGE=true ;;
    --pdf)   DO_PDF=true;  EXPLICIT_STAGE=true ;;
    --all)   DO_TEX=true; DO_HTML=true; DO_PDF=true; EXPLICIT_STAGE=true ;;
    --clean) DO_CLEAN=true ;;
    --force) DO_FORCE=true ;;
    *) error "Unknown option: '$arg'  (valid: --tex | --html | --pdf | --all | --clean | --force)" ;;
  esac
done

# Default: build all stages if none were explicitly requested
if ! $EXPLICIT_STAGE && ! $DO_CLEAN; then
  DO_TEX=true; DO_HTML=true; DO_PDF=true
fi

# ── Clean ──────────────────────────────────────────────────────────────────────
if $DO_CLEAN; then
  header "Cleaning generated and untracked files"
  rm -rf output/ latex/sections/ "$CACHE_LATEX" "$CACHE_DATA_HASH" "$CACHE_IMAGE_HASH"
  find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -name "*.pyc" -delete 2>/dev/null || true
  find latex -maxdepth 1 \( \
    -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.fls" \
    -o -name "*.fdb_latexmk" -o -name "*.synctex.gz" -o -name "*.bbl" \
    -o -name "*.blg" -o -name "*.xdv" \
  \) -delete 2>/dev/null || true
  find . -name ".DS_Store" -delete 2>/dev/null || true
  if $DO_FORCE; then
    rm -rf "$CACHE_FONTCONFIG"
    success "Full clean done (font cache also wiped)."
  else
    success "Font cache preserved in $CACHE_FONTCONFIG  (use --clean --force to wipe it too)"
    echo -e "${GREEN}✔  Clean done.${NC}"
  fi
  exit 0
fi

# ── Detect execution context ───────────────────────────────────────────────────
IN_CONTAINER="${RESUME_IN_DOCKER:-0}"

if [[ "$IN_CONTAINER" == "1" ]]; then
  # Inside Dev Container or Docker image — run scripts directly without Docker
  run() {
    local label="$1"; local cmd="$2"
    header "$label"
    eval "$cmd" || error "Stage failed: $label"
  }
else
  # Host machine — verify Docker is available and build the image
  command -v docker &>/dev/null || error "Docker not found. Install it from https://docs.docker.com/get-docker/"
  docker info &>/dev/null 2>&1        || error "Docker daemon is not running. Start Docker and try again."

  mkdir -p "$CACHE_DIR" "$CACHE_FONTCONFIG" "$CACHE_LATEX"

  # Smart image rebuild: skip docker build when Dockerfile + requirements.txt unchanged
  header "Building Docker image: $IMAGE"
  current_image_hash="$(sha256sum docker/Dockerfile requirements.txt | sha256sum | awk '{print $1}')"
  cached_image_hash="$(cat "$CACHE_IMAGE_HASH" 2>/dev/null || echo '')"
  if $DO_FORCE || [[ "$current_image_hash" != "$cached_image_hash" ]]; then
    DOCKER_BUILDKIT=0 docker build -f docker/Dockerfile -t "$IMAGE" . \
      || error "Docker build failed"
    echo "$current_image_hash" > "$CACHE_IMAGE_HASH"
  fi
  success "Image ready: $IMAGE"

  # run() — execute a command string inside a fresh container with the workspace mounted
  run() {
    local label="$1"; local cmd="$2"
    header "$label"
    docker run --rm \
      --entrypoint "" \
      -e HOME=/tmp \
      -e RESUME_IN_DOCKER=1 \
      -u "$(id -u):$(id -g)" \
      -v "$(pwd):/workspace" \
      -v "$(pwd)/$CACHE_FONTCONFIG:/tmp/.cache/fontconfig" \
      -w /workspace \
      "$IMAGE" bash -c "$cmd" \
      || error "Stage failed: $label"
  }
fi

# ── Hash-based skip for data-dependent stages ──────────────────────────────────
current_data_hash="$(sha256sum data/resume.yaml config/build.yaml | sha256sum | awk '{print $1}')"
cached_data_hash="$(cat "$CACHE_DATA_HASH" 2>/dev/null || echo '')"

SKIP_DATA=false
if ! $DO_FORCE && [[ "$current_data_hash" == "$cached_data_hash" ]]; then
  SKIP_DATA=true
fi

# ── Tex + HTML stages ──────────────────────────────────────────────────────────
if $DO_TEX && $DO_HTML; then
  if $SKIP_DATA; then
    warn "Data unchanged — skipping tex+html generation  (use --force to override)"
  else
    run \
      "Generating *.tex sections + HTML website" \
      "set -e
       python3 scripts/generate_latex.py
       python3 scripts/generate_html.py"
    echo "$current_data_hash" > "$CACHE_DATA_HASH"
  fi
elif $DO_TEX; then
  if $SKIP_DATA; then
    warn "Data unchanged — skipping tex generation  (use --force to override)"
  else
    run \
      "Generating *.tex sections  →  latex/sections/" \
      "set -e
       python3 scripts/generate_latex.py"
    echo "$current_data_hash" > "$CACHE_DATA_HASH"
  fi
elif $DO_HTML; then
  if $SKIP_DATA; then
    warn "Data unchanged — skipping html generation  (use --force to override)"
  else
    run \
      "Generating HTML website  →  output/html/" \
      "set -e
       python3 scripts/generate_html.py"
    echo "$current_data_hash" > "$CACHE_DATA_HASH"
  fi
fi

# ── PDF stage ──────────────────────────────────────────────────────────────────
# latexmk replaces double xelatex: auto-detects how many passes are needed
# and skips compilation entirely when no .tex files changed (uses .cache/latex/).
if $DO_PDF; then
  # Guard: sections must exist before latexmk can compile
  if ! compgen -G "latex/sections/*.tex" > /dev/null 2>&1; then
    error "latex/sections/*.tex not found — run ./build_all.sh or add --tex to generate them first"
  fi
  run \
    "Compiling PDFs  →  output/pdf/" \
    "set -e
     mkdir -p output/pdf $CACHE_LATEX
     cd latex
     latexmk -xelatex -interaction=nonstopmode -silent \
       -output-directory=../$CACHE_LATEX \
       main.tex
     cp ../$CACHE_LATEX/main.pdf ../output/pdf/main.pdf
     test -f ../output/pdf/main.pdf || { echo 'ERROR: main.pdf not produced'; exit 1; }
     cd ..
     bash scripts/compile_sections_pdf.sh $CACHE_LATEX"
fi

echo -e "\n${GREEN}✔  Done.${NC}"
