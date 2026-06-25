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
   - [latex/](#latex)
   - [web/](#web)
   - [scripts/](#scripts)
   - [docker/Dockerfile](#dockerdockerfile)
   - [build_all.sh](#build_allsh)
   - [output/](#output)
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

### `data/resume.yaml`

The **single source of truth**. Every piece of content in both the PDF and HTML
website comes from this file. Edit this; run `./build_all.sh`; done.

| Key | Description |
|---|---|
| `personal` | Name, title, email, phone, location, website, LinkedIn, GitHub, summary |
| `experience` | List of jobs — company, role, location, start/end dates, highlights |
| `education` | List of degrees — institution, degree, field, dates, GPA, highlights |
| `skills` | Map of category → list of items (`languages: [Python, Go]`) |
| `projects` | List of projects — name, URL, description, tech stack, highlights |
| `certifications` | List of certs — name, issuer, date, URL |
| `languages` | Spoken languages and proficiency levels |

Example structure:

```yaml
personal:
  name: Jane Doe
  title: Senior Software Engineer
  email: jane@example.com
  phone: "+84 000-000-0000"
  location: Ho Chi Minh City, Vietnam
  website: https://janedoe.dev
  linkedin: linkedin.com/in/janedoe
  github: github.com/janedoe
  summary: "Experienced engineer specialising in ..."

experience:
  - company: Acme Corp
    role: Senior Software Engineer
    location: Remote
    start: Jan 2022
    end: Present
    highlights:
      - Led migration from monolith to microservices, reducing deploy time by 60%.

skills:
  languages:  [Python, Go, TypeScript]
  frameworks: [FastAPI, React, Docker]
```

---

### `config/build.yaml`

Build-time settings. Rarely needs editing.

```yaml
compiler: xelatex       # LaTeX compiler used by latexmk
theme: default          # HTML theme (reserved for future use)
output_pdf: main.pdf    # Output filename for the full PDF
sections:               # Comment out a section to hide it from both PDF and HTML
  - header
  - experience
  - education
  - skills
  - projects
  - certifications
```

> **Note:** Hiding a section by commenting it out from `config/build.yaml` is not yet
> enforced by the generator scripts (known gap). As a workaround, remove the
> corresponding `\input` line from `latex/main.tex` (PDF) and the matching block
> from `web/templates/index.html` (HTML).

---

### `latex/`

| File | Purpose |
|---|---|
| `main.tex` | XeLaTeX entry point. Loads `styles/resume.sty` and `\input`s each section. Reorder `\input` lines to reorder PDF sections. |
| `section_standalone.tex` | Minimal wrapper for per-section PDF compilation. Uses `\jobname` trick: `latexmk -jobname=experience` → inputs `sections/experience.tex`. |
| `styles/resume.sty` | All visual design — page geometry, fonts (`fontspec`), colors, `\titleformat`, and the two key macros `\resumeheader{}` and `\resumeentry{}`. |
| `sections/*.tex` | **Auto-generated** from `data/resume.yaml`. Never edit by hand — overwritten on every build. |

---

### `web/`

| File | Purpose |
|---|---|
| `templates/index.html` | Jinja2 template. All YAML keys are injected via `template.render(**data)`. New top-level YAML keys are available immediately without Python changes. |
| `templates/components/` | Optional directory for reusable Jinja2 partials (`{% include "components/entry.html" %}`). |
| `static/css/style.css` | Responsive stylesheet with CSS custom properties, two-column skills grid, tag chips, and `@media print` rules for clean browser-to-PDF export. |

---

### `scripts/`

| File | Purpose |
|---|---|
| `generate_latex.py` | Reads `data/resume.yaml`, escapes LaTeX special chars via `esc()`, writes one `.tex` file per section into `latex/sections/`. |
| `generate_html.py` | Reads `data/resume.yaml`, renders `web/templates/index.html`, copies `web/static/` to `output/html/static/`. |
| `compile_sections_pdf.sh` | Loops over `latex/sections/*.tex`, compiles each with `latexmk -jobname=<name>`, copies result to `output/pdf/sections/<name>.pdf`. |
| `build.py` | Optional standalone CLI wrapper. Calls the Python generators and latexmk directly inside the container without `build_all.sh`. |

---

### `docker/Dockerfile`

Two-stage build that keeps the final image lean:

```
Stage 1 (python-deps):  python:3.12-slim
  └── COPY requirements.txt + pip install (PyYAML, Jinja2)

Stage 2 (runtime):      python:3.12-slim
  ├── apt install: texlive-xetex texlive-latex-extra texlive-fonts-recommended
  │               fonts-lmodern latexmk
  ├── COPY site-packages from Stage 1
  ├── WORKDIR /workspace
  ├── ENV RESUME_IN_DOCKER=1
  └── ENTRYPOINT ["bash", "build_all.sh"]
```

> **ENTRYPOINT quirk:** Because the image sets `ENTRYPOINT ["bash", "build_all.sh"]`,
> all `docker run` calls in `build_all.sh` must use `--entrypoint ""` to override it,
> otherwise Docker prepends the entrypoint and passes your command as arguments to
> `build_all.sh`.

---

### `build_all.sh`

The single entry point. Responsibilities:

1. **Parse flags** — `--tex`, `--html`, `--pdf`, `--all`, `--clean`, `--force`
2. **Detect context** — if `RESUME_IN_DOCKER=1`, run scripts directly; otherwise use Docker
3. **Smart image rebuild** — hash `Dockerfile + requirements.txt`; skip `docker build` on cache hit
4. **Hash-based skip** — hash `resume.yaml + config/build.yaml`; skip Python generation when data unchanged
5. **Combined run** — when both `--tex` and `--html` are needed, run in a single container (saves startup time)
6. **PDF compilation** — `latexmk` (smart multi-pass) for `main.pdf`, then `compile_sections_pdf.sh` for per-section PDFs
7. **Cache mounts** — `.cache/fontconfig` and `.cache/latex` are mounted into the container for persistence

---

### `output/`

Git-ignored by default. Commit only if publishing via GitHub Pages.

| Path | Contents |
|---|---|
| `output/pdf/main.pdf` | Full print-ready resume |
| `output/pdf/sections/<name>.pdf` | Individual section PDFs (one per section) |
| `output/html/index.html` | Resume website |
| `output/html/static/` | CSS and assets copied from `web/static/` |

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
