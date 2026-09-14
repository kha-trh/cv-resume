# Copilot Instructions

This repository is a Docker-powered, data-driven resume generator. The project is intentionally simple: edit the YAML source, then rebuild the generated PDF/HTML assets.

For the full project documentation, see [README.md](../README.md).

## Operating rules for AI agents

- Treat [data/resume.yaml](../data/resume.yaml) as the single source of truth for all content changes.
- Do not hand-edit generated files under [latex/sections](../latex/sections); they are overwritten by the build pipeline.
- Prefer tweaking styling in [latex/styles/resume.sty](../latex/styles/resume.sty) or the document structure in [latex/main.tex](../latex/main.tex) for layout issues.
- Use [config/build.yaml](../config/build.yaml) to enable or disable sections; do not remove generator functions unless the feature is intentionally being retired.
- If you add a new top-level YAML key, it becomes available in the HTML template automatically via Jinja2 rendering.

## Build commands

```bash
./build_all.sh           # default: generate *.tex + HTML + PDF
./build_all.sh --tex     # regenerate LaTeX section files only
./build_all.sh --html    # render the HTML site only
./build_all.sh --pdf     # compile main.pdf + per-section PDFs
./build_all.sh --clean   # remove generated output and cache metadata
./build_all.sh --force   # bypass cached data and rebuild everything
```

Docker is the only host dependency; the builder image is created automatically when needed. The project uses cached builds and incremental LaTeX compilation in `.cache/`.

## Typical workflow

1. Update [data/resume.yaml](../data/resume.yaml) for personal info, experience, skills, projects, etc.
2. If a section should be hidden, comment it out in [config/build.yaml](../config/build.yaml).
3. Run the smallest relevant build command:
   - `./build_all.sh --tex` for content-only generation
   - `./build_all.sh --html` for the website output
   - `./build_all.sh --pdf` for the PDF output
   - `./build_all.sh` for the full pipeline
4. Validate the generated outputs in [output/pdf](../output/pdf) and [output/html](../output/html).

## Project-specific conventions

- [scripts/generate_latex.py](../scripts/generate_latex.py) converts YAML data into section .tex files and must escape LaTeX-special characters via `esc()` before writing text.
- [scripts/generate_html.py](../scripts/generate_html.py) renders [web/templates/index.html](../web/templates/index.html) with Jinja2 using `template.render(**data)`.
- The PDF entry point is [latex/main.tex](../latex/main.tex); section order in the compiled PDF follows the `\input{sections/...}` lines there.
- The per-section PDF workflow is driven by [latex/section_standalone.tex](../latex/section_standalone.tex) and [scripts/compile_sections_pdf.sh](../scripts/compile_sections_pdf.sh).
- Keep [docker/Dockerfile](../docker/Dockerfile) and [requirements.txt](../requirements.txt) in sync when changing the build environment.

## When making changes

- Prefer data edits over structural edits unless the requirement is clearly a template/style change.
- Always validate with the project’s build commands rather than manual output patches.
- Preserve the repo’s convention of generated assets living under [output](../output) and source data living under [data](../data) and [config](../config).
