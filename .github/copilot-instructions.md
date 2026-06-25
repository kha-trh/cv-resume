# Copilot Instructions

## Build Commands

```bash
./build_all.sh           # generate everything: *.tex + HTML + PDF (default)
./build_all.sh --tex     # regenerate latex/sections/*.tex only
./build_all.sh --html    # render HTML website only
./build_all.sh --pdf     # compile main.pdf + per-section PDFs in output/pdf/sections/
./build_all.sh --all     # explicit alias for the default
./build_all.sh --clean   # remove all generated/cached files (output/, latex/sections/, .cache/latex/, hash files)
./build_all.sh --force   # bypass all caches and rebuild everything
```

Every invocation rebuilds the Docker image if needed (instant on cache hit). No Python or LaTeX installation required on the host — Docker is the only dependency.

To run a single stage directly inside the container without going through `build_all.sh`:

```bash
docker run --rm --entrypoint "" -e HOME=/tmp \
  -v "$(pwd):/workspace" -u "$(id -u):$(id -g)" -w /workspace \
  resume-builder python3 scripts/generate_latex.py
```

## Build Cache

`.cache/` (git-ignored) persists between runs:

| Path | Contents | Effect |
|---|---|---|
| `.cache/fontconfig/` | fontconfig font cache | xelatex finds fonts without rebuilding cache each run |
| `.cache/latex/` | latexmk aux + `.fdb_latexmk` for `main.tex` | latexmk skips xelatex passes when `.tex` files unchanged |
| `.cache/latex/sections/` | latexmk aux + `.fdb_latexmk` per section | per-section PDF compilation is incremental |
| `.cache/data.sha256` | hash of `resume.yaml` + `config/build.yaml` | skips Python generation steps when data unchanged |
| `.cache/image.sha256` | hash of `Dockerfile` + `requirements.txt` | skips `docker build` when image definition unchanged |

`--clean` removes `output/`, `latex/sections/`, `.cache/latex/`, and hash files but **keeps `.cache/fontconfig/`** for fast subsequent builds. Use `--clean --force` to also wipe the font cache.

## Architecture

This is a **data-driven document pipeline**:

```
data/resume.yaml  ──►  scripts/generate_latex.py  ──►  latex/sections/*.tex  ──►  output/pdf/main.pdf
                  │                                                             └──►  output/pdf/sections/<name>.pdf  (per section)
                  └──►  scripts/generate_html.py   ──►  output/html/index.html
```

- **`data/resume.yaml`** is the single source of truth. All content in both the PDF and HTML site originates here.
- **`config/build.yaml`** controls build settings and which sections are active. Commenting out an entry under `sections:` hides that section from both outputs.
- **`scripts/generate_latex.py`** reads the YAML and writes one `.tex` file per section into `latex/sections/`. It uses the `esc()` helper to escape LaTeX special characters.
- **`scripts/generate_html.py`** renders `web/templates/index.html` (a Jinja2 template) with `template.render(**data)`, so every top-level YAML key is a direct template variable (e.g., `{{ personal.name }}`, `{% for job in experience %}`).
- **`latex/main.tex`** is the XeLaTeX entry point; section order in the PDF is controlled by the order of `\input{sections/...}` lines here.
- **`latex/section_standalone.tex`** is a minimal wrapper used for per-section PDF compilation. It uses the `\jobname` trick (`\edef\sectionfile{sections/\jobname}\input{\sectionfile}`) so `latexmk -jobname=experience section_standalone.tex` compiles only `sections/experience.tex`.
- **`scripts/compile_sections_pdf.sh`** loops over every `latex/sections/*.tex`, compiles each via `latexmk -jobname=<name>`, and copies the result to `output/pdf/sections/<name>.pdf`. Uses `.cache/latex/sections/` for incremental compilation.
- **`latex/styles/resume.sty`** defines all visual design: fonts, colors, margins, and the two key macros `\resumeheader{...}` and `\resumeentry{...}` used in every generated section file.

## Key Conventions

### Never edit `latex/sections/` by hand
These files are **overwritten on every build**. All content changes must go into `data/resume.yaml`; all structural/macro changes go into `latex/styles/resume.sty` or `latex/main.tex`.

### LaTeX escaping
Any text from YAML that appears in LaTeX must pass through `esc()` in `generate_latex.py`. When adding a new generator function, always call `esc()` on user-provided strings.

### Jinja2 template variables
`generate_html.py` calls `template.render(**data)` with `autoescape=False`. Every top-level YAML key becomes a template variable. New top-level keys added to `resume.yaml` are immediately available in `web/templates/index.html`.

### Two-pass XeLaTeX / latexmk
The PDF build uses `latexmk -xelatex` which automatically determines how many passes are needed (typically 2 for cross-references). Aux files are cached in `.cache/latex/` and `.cache/latex/sections/` so unchanged sections are skipped on subsequent runs.

### Section visibility
To hide a section from both PDF and HTML, comment it out in `config/build.yaml` under `sections:`. The generator scripts respect this list; do not delete section generator functions in `generate_latex.py`.

### Per-section PDFs
`scripts/compile_sections_pdf.sh` compiles every file in `latex/sections/` as a standalone PDF using `latex/section_standalone.tex` as the wrapper. When adding a new section generator in `generate_latex.py`, no changes to `compile_sections_pdf.sh` are needed — the glob `latex/sections/*.tex` picks it up automatically. The `\jobname` trick requires the section file to be in `sections/<name>.tex` and the name must not contain spaces.

### `.dockerignore` must stay at repo root
Docker resolves `.dockerignore` relative to the build context (`docker build ... .`), not the Dockerfile location (`docker/Dockerfile`). Moving it will bloat the build context.
