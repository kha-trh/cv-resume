# Resume / CV Workspace

A **Docker-powered, data-driven** workspace for building a professional resume/CV.
Edit **one YAML file** — the build system generates a print-ready **PDF** (via XeLaTeX)
and a **static HTML website** automatically.  
Zero host dependencies beyond Docker.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Build Commands](#build-commands)
3. [Build Process Workflow](#build-process-workflow)
4. [Software Architecture](#software-architecture)
5. [Repo Structure](#repo-structure)
6. [File Reference](#file-reference)
   - [data/resume.yaml](#dataresumeyaml)
   - [config/build.yaml](#configbuildyaml)
   - [build_all.sh](#build_allsh)
   - [docker/Dockerfile](#dockerdockerfile)
   - [requirements.txt](#requirementstxt)
   - [latex/main.tex](#latexmaintex)
   - [latex/section_standalone.tex](#latexsection_standalonetex)
   - [latex/styles/resume.sty](#latexstylesresumesty)
   - [scripts/generate_latex.py](#scriptsgenerate_latexpy)
   - [scripts/generate_html.py](#scriptsgenerate_htmlpy)
   - [scripts/compile_sections_pdf.sh](#scriptscompile_sections_pdfsh)
   - [scripts/build.py](#scriptsbuildpy)
   - [web/templates/index.html](#webtemplatesindexhtml)
   - [web/static/css/style.css](#webstaticcssstylecss)
   - [.github/copilot-instructions.md](#githubcopilot-instructionsmd)
   - [.github/skills/](#githubskills)
   - [.gitmessage.txt](#gitmessagetxt)
   - [.gitignore](#gitignore)
   - [.dockerignore](#dockerignore)
   - [.vscode/settings.json](#vscodesettingsjson)
7. [Build Cache](#build-cache)
8. [Customising the Design](#customising-the-design)
9. [Publishing the HTML Site](#publishing-the-html-site)

---

## Quick Start

```bash
# 1. Install Docker → https://docs.docker.com/get-docker/

# 2. Fill in your details — the ONLY file you need to edit
$EDITOR data/resume.yaml

# 3. Build everything
./build_all.sh
#    → output/pdf/main.pdf            (full resume PDF)
#    → output/pdf/sections/*.pdf      (one PDF per section)
#    → output/html/index.html         (static website)
```

No Python, no LaTeX, no package managers required on your machine.

---

## Build Commands

| Command | What it does |
|---|---|
| `./build_all.sh` | Generate everything — tex + HTML + PDF (default) |
| `./build_all.sh --all` | Explicit alias for the default |
| `./build_all.sh --tex` | Regenerate `latex/sections/*.tex` only |
| `./build_all.sh --html` | Render HTML website only |
| `./build_all.sh --pdf` | Compile `main.pdf` + per-section PDFs |
| `./build_all.sh --clean` | Delete all generated/cached files |
| `./build_all.sh --force` | Bypass all caches, rebuild from scratch |
| `./build_all.sh --clean --force` | Full reset including font cache |

Flags can be combined: `./build_all.sh --pdf --force`

---

## Build Process Workflow

```
./build_all.sh [flags]
│
├─ Detect execution context
│   ├─ RESUME_IN_DOCKER=1  (VS Code Dev Container or inside Docker image)
│   │   └─ scripts and xelatex invoked directly — no nested Docker
│   └─ Host machine
│       ├─ verify: docker found + daemon running
│       └─ docker build  (skipped on cache hit via Dockerfile hash)
│
├─ --clean ─────► remove output/  latex/sections/  .cache/latex/  hash files
│   --force        also remove .cache/fontconfig/                   → EXIT
│
├─ Hash check: sha256(resume.yaml + config/build.yaml)
│   └─ unchanged + no --force  →  skip tex/html stages (instant)
│
├─ --tex ───────► [docker run]  python3 scripts/generate_latex.py
│                   reads  : data/resume.yaml
│                   writes : latex/sections/header.tex
│                            latex/sections/experience.tex
│                            latex/sections/education.tex
│                            latex/sections/skills.tex
│                            latex/sections/projects.tex
│                            latex/sections/certifications.tex
│
├─ --html ──────► [docker run]  python3 scripts/generate_html.py
│                   reads  : data/resume.yaml
│                   renders: web/templates/index.html  (Jinja2)
│                   writes : output/html/index.html
│                   copies : web/static/  →  output/html/static/
│
└─ --pdf ───────► [docker run]
    ├─ latexmk -xelatex  (smart multi-pass, cache in .cache/latex/)
    │   reads  : latex/main.tex + latex/sections/*.tex + latex/styles/resume.sty
    │   writes : output/pdf/main.pdf
    └─ scripts/compile_sections_pdf.sh
        reads  : latex/section_standalone.tex + latex/sections/<name>.tex
        cache  : .cache/latex/sections/
        writes : output/pdf/sections/<name>.pdf  (one per section)
```

> **Dev Container:** When developing inside VS Code Dev Container, `RESUME_IN_DOCKER=1`
> is set automatically — `build_all.sh` runs scripts directly without spawning Docker.

---

## Software Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                              │
│                                                                       │
│  docker/Dockerfile  →  resume-builder image                          │
│  python:3.12-slim + texlive-xetex + latexmk + PyYAML + Jinja2       │
│  Workspace bind-mounted at /workspace inside container               │
│  ENV RESUME_IN_DOCKER=1  (lets build_all.sh skip Docker inside)      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                 │
│                                                                       │
│  data/resume.yaml    ←  single source of truth (all content)        │
│  data/assets/        ←  images & icons                               │
│  config/build.yaml   ←  compiler, theme, active section list         │
└───────────────┬──────────────────────────┬───────────────────────────┘
                │ PyYAML                    │ PyYAML
                ▼                           ▼
┌──────────────────────────────┐  ┌─────────────────────────────────────┐
│         PDF PIPELINE         │  │           HTML PIPELINE              │
│                              │  │                                      │
│  scripts/generate_latex.py   │  │  scripts/generate_html.py            │
│  ┌────────────────────────┐  │  │  ┌─────────────────────────────────┐ │
│  │  gen_header()          │  │  │  │  Jinja2 Environment             │ │
│  │  gen_experience()      │  │  │  │  template.render(**data)        │ │
│  │  gen_education()       │  │  │  │  all YAML keys → template vars  │ │
│  │  gen_skills()          │  │  │  └──────────────┬──────────────────┘ │
│  │  gen_projects()        │  │  │                 │                    │
│  │  gen_certifications()  │  │  │                 ▼                    │
│  │  esc()  ← LaTeX escape │  │  │  web/templates/index.html           │
│  └───────────┬────────────┘  │  │  web/static/  (css, js, images)    │
│              │               │  │                 │                    │
│              ▼               │  │                 ▼                    │
│  latex/sections/*.tex        │  │  output/html/index.html             │
│  (⚠ auto-generated)          │  │  output/html/static/                │
│              │               │  └─────────────────────────────────────┘
│  latex/main.tex              │
│  (section order + includes)  │
│  latex/styles/resume.sty     │
│  (fonts · colors · macros)   │
│  latex/section_standalone.tex│
│  (per-section wrapper)       │
│              │               │
│              ▼               │
│  latexmk -xelatex            │
│  (smart multi-pass, cached)  │
│              │               │
│              ├──────────────►  output/pdf/main.pdf
│              └──────────────►  output/pdf/sections/<name>.pdf
└──────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                           CACHE LAYER                                 │
│                                                                       │
│  .cache/fontconfig/    font cache  →  warm xelatex starts           │
│  .cache/latex/         latexmk aux →  skips passes when unchanged   │
│  .cache/latex/sections/ per-section latexmk aux                     │
│  .cache/data.sha256    data hash   →  skips Python steps            │
│  .cache/image.sha256   image hash  →  skips docker build            │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design rules:**
- `data/resume.yaml` is the **only** file with user content — both pipelines read from it.
- `latex/sections/` is **always overwritten** by `generate_latex.py`; never edit those files by hand.
- `latex/main.tex` controls **section order** in the PDF — reorder the `\input` lines to reorder sections.
- The HTML template receives every top-level YAML key as a variable; new keys are available immediately.
- The `\jobname` trick in `section_standalone.tex` allows compiling any single section as a standalone PDF without duplicating the document preamble.

---

## Repo Structure

```
resume/
│
├── data/                            ← THE ONLY FOLDER YOU REGULARLY EDIT
│   ├── resume.yaml                  ← Single source of truth for all content
│   └── assets/
│       ├── images/                  ← Profile photo, embedded images
│       └── icons/                   ← Custom SVG/PNG icons
│
├── config/
│   └── build.yaml                   ← Build settings (compiler, theme, sections)
│
├── latex/                           ← LaTeX source → PDF output
│   ├── main.tex                     ← Master document (XeLaTeX entry point)
│   ├── section_standalone.tex       ← Wrapper for per-section PDF compilation
│   ├── styles/
│   │   └── resume.sty               ← Fonts, colors, margins, macros
│   └── sections/                    ← ⚠ AUTO-GENERATED — do not edit by hand
│       ├── header.tex
│       ├── experience.tex
│       ├── education.tex
│       ├── skills.tex
│       ├── projects.tex
│       └── certifications.tex
│
├── web/                             ← HTML website source
│   ├── templates/
│   │   ├── index.html               ← Jinja2 template (layout & structure)
│   │   └── components/              ← Reusable Jinja2 partials (optional)
│   └── static/
│       ├── css/
│       │   └── style.css            ← Responsive + print-friendly stylesheet
│       ├── js/                      ← Optional JavaScript
│       └── images/                  ← Web-specific images (favicon, OG image)
│
├── scripts/                         ← Build scripts (run inside Docker)
│   ├── generate_latex.py            ← resume.yaml → latex/sections/*.tex
│   ├── generate_html.py             ← resume.yaml + template → output/html/
│   ├── compile_sections_pdf.sh      ← Compiles each section as standalone PDF
│   └── build.py                     ← Optional CLI wrapper (direct container use)
│
├── output/                          ← ⚠ GENERATED — git-ignored
│   ├── pdf/
│   │   ├── main.pdf                 ← Full resume PDF
│   │   └── sections/                ← Per-section PDFs
│   │       ├── header.pdf
│   │       ├── experience.pdf
│   │       ├── education.pdf
│   │       ├── skills.pdf
│   │       ├── projects.pdf
│   │       └── certifications.pdf
│   └── html/
│       ├── index.html               ← Rendered website
│       └── static/                  ← Copied from web/static/
│
├── docker/
│   └── Dockerfile                   ← Two-stage image (Python deps + TeX + runtime)
│
├── .cache/                          ← ⚠ GENERATED — git-ignored (build caches)
│   ├── fontconfig/                  ← XeLaTeX font cache
│   ├── latex/                       ← latexmk aux files (main + sections)
│   ├── data.sha256                  ← Hash of resume.yaml + build.yaml
│   └── image.sha256                 ← Hash of Dockerfile + requirements.txt
│
├── .devcontainer/
│   └── devcontainer.json            ← VS Code Dev Container config
│
├── .github/
│   └── copilot-instructions.md      ← Copilot context (build commands, conventions)
│
├── .vscode/
│   └── settings.json                ← Forces xelatex recipe in LaTeX Workshop
│
├── .dockerignore                    ← Excludes output/, .git/, etc. from build context
├── .gitignore                       ← Ignores output/, .cache/, latex/sections/
├── build_all.sh                     ← Single entry point — run this
└── requirements.txt                 ← Python deps (PyYAML, Jinja2)
```

---

## File Reference

This section documents all primary files in the workspace using a consistent format.

## data/resume.yaml

### Description
The single source of truth for all resume and CV content. It contains structured personal information, work experience, educational history, technical skills, projects, certifications, and language proficiencies.

### How to Use
Edit this file directly whenever resume information changes. Ensure YAML syntax and indentation remain valid. Strings containing special characters (such as colons or ampersands) should be quoted. Run `./build_all.sh` after editing to rebuild both the PDF and HTML outputs.

### Where It Is Used
- Read by [scripts/generate_latex.py](scripts/generate_latex.py) to generate [latex/sections](latex/sections) .tex files.
- Read by [scripts/generate_html.py](scripts/generate_html.py) to render [output/html/index.html](output/html/index.html).
- Hashed by [build_all.sh](build_all.sh) to determine whether regeneration stages can be skipped.

---

## config/build.yaml

### Description
Defines build configuration settings and section visibility. Configures compiler selection (such as XeLaTeX), default theme, target PDF file name, and the active list of document sections.

### How to Use
Configure compiler options or adjust the list of active sections (`sections`). To temporarily disable a section from generation, comment it out under the `sections` list.

### Where It Is Used
- Read and hashed by [build_all.sh](build_all.sh) for caching and build-change detection.
- Referenced by build tools and documentation to manage section visibility.

---

## build_all.sh

### Description
The primary build orchestration script and single entry point for all build and clean operations. Manages Docker image verification/building, hash-based caching, selective target building (`--tex`, `--html`, `--pdf`), and artifact cleanup.

### How to Use
Execute from the repository root:
- `./build_all.sh` (default full build: TeX sections, HTML site, and compiled PDFs)
- `./build_all.sh --tex` (generate LaTeX section files only)
- `./build_all.sh --html` (render HTML website only)
- `./build_all.sh --pdf` (compile master and section PDFs only)
- `./build_all.sh --force` (bypass caches and rebuild everything)
- `./build_all.sh --clean` (remove build outputs and LaTeX caches)
- `./build_all.sh --clean --force` (wipe all outputs including font cache)

### Where It Is Used
- Run directly by users in the terminal or CI/CD pipelines.
- Executed inside the container runtime environment when `RESUME_IN_DOCKER=1` is set.

---

## docker/Dockerfile

### Description
Defines the multi-stage Docker build environment for generating resume outputs with zero host dependencies. Stage 1 installs Python dependencies (PyYAML, Jinja2), and Stage 2 installs Debian TeX Live packages (`texlive-xetex`, `latexmk`, `fonts-lmodern`), fonts, and runtime tools.

### How to Use
Built automatically by [build_all.sh](build_all.sh) on first run or when dependencies change. Can also be built manually using `docker build -f docker/Dockerfile -t resume-builder .`.

### Where It Is Used
- Referenced and built by [build_all.sh](build_all.sh).
- Tracked for cache invalidation via `.cache/image.sha256`.

---

## requirements.txt

### Description
Lists pinned Python library dependencies required by the data extraction and HTML templating scripts.

### How to Use
Installed into the Docker image during container build via `pip install --no-cache-dir -r requirements.txt`. If modifying, keep in sync with [docker/Dockerfile](docker/Dockerfile).

### Where It Is Used
- Copied and installed in [docker/Dockerfile](docker/Dockerfile).
- Hashed by [build_all.sh](build_all.sh) to detect dependency updates.

---

## latex/main.tex

### Description
Master XeLaTeX entry document for the complete resume PDF. Configures document geometry and styling via `styles/resume.sty` and includes each generated section in sequence using `\input{sections/...}`.

### How to Use
Controls the ordering of sections in the generated master PDF. To change the visual order of sections in the PDF, reorder the `\input{sections/...}` statements in this file.

### Where It Is Used
- Compiled by `latexmk` within [build_all.sh](build_all.sh) and [scripts/build.py](scripts/build.py).
- Produces the primary output file [output/pdf/main.pdf](output/pdf/main.pdf).

---

## latex/section_standalone.tex

### Description
A lightweight XeLaTeX wrapper template used to compile any individual section .tex file into an independent standalone PDF document. Uses `\jobname` to dynamically input `sections/\jobname.tex`.

### How to Use
Invoked programmatically by [scripts/compile_sections_pdf.sh](scripts/compile_sections_pdf.sh) with `latexmk -jobname=<section_name> latex/section_standalone.tex`.

### Where It Is Used
- Consumed by [scripts/compile_sections_pdf.sh](scripts/compile_sections_pdf.sh) to produce per-section PDFs in [output/pdf/sections/](output/pdf/sections/).

---

## latex/styles/resume.sty

### Description
Custom LaTeX package defining visual design, page geometry, typography, color palettes, section heading rules, list spacing, and core macros (`\resumeheader`, `\resumeentry`, `\skillrow`).

### How to Use
Imported in LaTeX documents via `\usepackage{styles/resume}`. Modify this file to customize margins, accent colors, fonts, line heights, or entry layouts.

### Where It Is Used
- Included in [latex/main.tex](latex/main.tex) and [latex/section_standalone.tex](latex/section_standalone.tex).
- Formats every generated section file under `latex/sections/`.

---

## scripts/generate_latex.py

### Description
Python script that reads [data/resume.yaml](data/resume.yaml), escapes LaTeX special characters using `esc()`, and outputs modular LaTeX files into `latex/sections/` (`header.tex`, `experience.tex`, `education.tex`, `skills.tex`, `projects.tex`, `certifications.tex`, `languages.tex`).

### How to Use
Executed as part of the build pipeline via `python3 scripts/generate_latex.py` or through `./build_all.sh --tex`. Requires `pyyaml`.

### Where It Is Used
- Called by [build_all.sh](build_all.sh) during the TeX generation stage.
- Called by [scripts/build.py](scripts/build.py) when building standalone inside the container.
- Populates `latex/sections/*.tex` for compilation by `latexmk`.

---

## scripts/generate_html.py

### Description
Python script that loads [data/resume.yaml](data/resume.yaml), renders [web/templates/index.html](web/templates/index.html) using Jinja2, outputs [output/html/index.html](output/html/index.html), and synchronizes static assets from [web/static/](web/static/) to [output/html/static/](output/html/static/).

### How to Use
Executed as part of the build pipeline via `python3 scripts/generate_html.py` or through `./build_all.sh --html`. Requires `pyyaml` and `jinja2`.

### Where It Is Used
- Called by [build_all.sh](build_all.sh) during the HTML generation stage.
- Called by [scripts/build.py](scripts/build.py) when rendering website output.
- Generates the deployable web bundle in [output/html/](output/html/).

---

## scripts/compile_sections_pdf.sh

### Description
Bash script that iterates over all generated files in `latex/sections/*.tex`, compiles each as an independent PDF using [latex/section_standalone.tex](latex/section_standalone.tex) and `latexmk`, and copies the outputs to `output/pdf/sections/`.

### How to Use
Invoked automatically by [build_all.sh](build_all.sh) during the PDF stage, or directly via `bash scripts/compile_sections_pdf.sh [cache_dir]`.

### Where It Is Used
- Called by [build_all.sh](build_all.sh) to compile per-section PDFs in [output/pdf/sections/](output/pdf/sections/).

---

## scripts/build.py

### Description
Optional Python CLI utility that chains LaTeX generation, HTML rendering, and XeLaTeX compilation in sequence for developers working directly inside the container or virtual environment.

### How to Use
Run inside the container: `python3 scripts/build.py [--tex] [--html] [--pdf]`. When invoked without flags, it executes all stages sequentially.

### Where It Is Used
- Used as an alternative direct CLI runner inside containerized development environments.

---

## web/templates/index.html

### Description
Primary Jinja2 HTML layout template for the resume website. Renders personal details, work experience roles, education, technical skill tags, project responsibilities and highlights, certifications, and language proficiencies.

### How to Use
Edit this file to modify website markup structure, semantic HTML tags, or Jinja2 template conditionals. Changes are rendered to [output/html/index.html](output/html/index.html) on the next HTML build.

### Where It Is Used
- Loaded and rendered by [scripts/generate_html.py](scripts/generate_html.py).
- Produced as [output/html/index.html](output/html/index.html).

---

## web/static/css/style.css

### Description
Responsive stylesheet for the resume website. Provides CSS custom property variables, clean typography, entry cards, tag chips for skills/tech, and print styles (`@media print`) for clean browser export.

### How to Use
Edit this file to customize web colors, layout spacing, typography, and responsive breakpoints. Copied alongside HTML output during builds.

### Where It Is Used
- Linked in [web/templates/index.html](web/templates/index.html).
- Copied by [scripts/generate_html.py](scripts/generate_html.py) to [output/html/static/css/style.css](output/html/static/css/style.css).

---

## .github/copilot-instructions.md

### Description
Provides guidelines and operational rules for AI assistants working in this repository. Details architecture principles, single-source-of-truth rules, build commands, and coding conventions.

### How to Use
Read automatically by GitHub Copilot and coding agents when assisting in the repository workspace.

### Where It Is Used
- Read by AI agents and developer tooling across chat and automated workflows.

---

## .github/skills/resume-commit/SKILL.md

### Description
Defines the `/resume-commit` agent skill. Guides reviewing staged Git changes, formatting conventional commit messages according to [.gitmessage.txt](.gitmessage.txt), and proposing structured commit messages.

### How to Use
Invoked in Copilot chat using `/resume-commit` when preparing Git commits for staged or modified resume changes.

### Where It Is Used
- Loaded by GitHub Copilot when generating or validating Git commit messages.

---

## .github/skills/resume-content-editing/SKILL.md

### Description
Defines the `/resume-content-editing` agent skill. Enforces data-driven content editing rules, YAML schema structure, bullet point standards, and build validation steps for [data/resume.yaml](data/resume.yaml).

### How to Use
Invoked in Copilot chat when updating personal information, experience, projects, or skill sections in the resume data.

### Where It Is Used
- Loaded by GitHub Copilot when performing resume content updates.

---

## .github/skills/resume-doc-sync/SKILL.md

### Description
Defines the `/resume-doc-sync` agent skill. Directs auditing and synchronizing content parity and formatting consistency between the generated PDF documentation and the HTML website.

### How to Use
Invoked in Copilot chat when verifying schema consistency, template variables, and generator alignment between PDF and web outputs.

### Where It Is Used
- Loaded by GitHub Copilot when auditing output consistency and synchronization across build pipelines.

---

## .gitmessage.txt

### Description
Repository Git commit message template defining Conventional Commits conventions, allowed types (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`), subject length limits (72 characters), body formatting, and footers.

### How to Use
Configure Git to use this template via `git config commit.template .gitmessage.txt`. Referenced when writing commit messages manually or via AI skills.

### Where It Is Used
- Referenced by [.github/skills/resume-commit/SKILL.md](.github/skills/resume-commit/SKILL.md).
- Displayed by Git when preparing commit messages interactively.

---

## .gitignore

### Description
Specifies intentionally untracked files and directories to ignore in version control, including build outputs (`output/`), build caches (`.cache/`), auto-generated LaTeX sections (`latex/sections/`), and temporary compiler artifacts.

### How to Use
Updated when adding new cache directories, local IDE configurations, or build output locations that should not be committed to Git.

### Where It Is Used
- Enforced by Git during staging, status checks, and commit operations.

---

## .dockerignore

### Description
Specifies files and folders to exclude from the Docker build context when assembling the `resume-builder` container image, preventing large caches and generated files from inflating build context transfer.

### How to Use
Maintained at the repository root to exclude `.git/`, `output/`, `.cache/`, and local temporary files from Docker image builds.

### Where It Is Used
- Processed by the Docker daemon during `docker build` commands executed in [build_all.sh](build_all.sh).

---

## .vscode/settings.json

### Description
VS Code workspace configuration file that sets default LaTeX Workshop recipes to use XeLaTeX for document compilation.

### How to Use
Automatically applied by VS Code when opening this workspace with the LaTeX Workshop extension installed.

### Where It Is Used
- Used by the VS Code editor and LaTeX Workshop extension.

---

## Build Cache

`.cache/` persists between runs and is git-ignored:

| Path | What's cached | Benefit |
|---|---|---|
| `.cache/fontconfig/` | XeLaTeX font index | Eliminates font-scan overhead on every run |
| `.cache/latex/` | latexmk aux + `.fdb_latexmk` | Skips unnecessary xelatex passes when `.tex` unchanged |
| `.cache/latex/sections/` | Per-section latexmk aux | Incremental per-section PDF compilation |
| `.cache/data.sha256` | Hash of `resume.yaml` + `config/build.yaml` | Skips Python generation when data unchanged |
| `.cache/image.sha256` | Hash of `Dockerfile` + `requirements.txt` | Skips `docker build` when image definition unchanged |

**Typical timings:**

| Scenario | Time |
|---|---|
| First run (cold, no image) | ~5–10 min (downloads TeX packages) |
| After image built, data changed | ~10–20 s |
| Data unchanged (cache hit) | ~1–2 s |
| `--force` rebuild | ~10–20 s |

`--clean` removes generated files and `.cache/latex/` but **preserves `.cache/fontconfig/`**
(expensive to rebuild). Use `--clean --force` for a full reset.

---

## Customising the Design

| Goal | File to edit |
|---|---|
| Change PDF fonts, colors, or margins | `latex/styles/resume.sty` |
| Reorder sections in the PDF | `latex/main.tex` — reorder `\input` lines |
| Change HTML layout or add sections | `web/templates/index.html` |
| Change HTML colors, spacing, typography | `web/static/css/style.css` |
| Add a new content section | `data/resume.yaml` → `scripts/generate_latex.py` → `latex/main.tex` |

---

## Publishing the HTML Site

After `./build_all.sh`, `output/html/` is a self-contained static site:

```bash
# GitHub Pages — serve from /docs
cp -r output/html/* docs/
git add docs/ && git commit -m "publish resume" && git push
# Repository Settings → Pages → set source to /docs

# Netlify / Vercel / Cloudflare Pages
# Set publish directory to output/html/
```

---

## License

This workspace template is yours to use freely.  
Replace all placeholder content in `data/resume.yaml` with your own information.
