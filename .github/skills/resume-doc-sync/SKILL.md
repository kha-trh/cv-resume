---
name: resume-doc-sync
description: "Use when: synchronizing PDF and website outputs, auditing consistency between LaTeX and HTML generators/templates, ensuring data schema parity across data/resume.yaml, scripts/generate_latex.py, and web/templates/index.html, or validating build outputs."
---

# Resume Documentation & Output Synchronization

Audit, align, and synchronize the generated PDF and website outputs from the single source of truth (`data/resume.yaml`).

## Objective

Ensure semantic, informational, and structural consistency between the compiled PDF (`output/pdf/main.pdf`) and the web output (`output/html/index.html`) without duplicating content or breaking target-specific formatting.

## Workflow

### 1. Inspect Sources and Configurations
- Review `data/resume.yaml` (single source of truth for resume data).
- Review `config/build.yaml` (enabled sections and build configurations).
- Review `latex/main.tex`, `latex/section_standalone.tex`, and `latex/styles/resume.sty`.
- Review generation scripts: `scripts/generate_latex.py`, `scripts/generate_html.py`, `scripts/build.py`, and `build_all.sh`.
- Review templates and styles: `web/templates/index.html`, `web/static/css/style.css`.

### 2. Audit Output Parity & Identify Discrepancies
Compare PDF generator logic and HTML template logic across each section:
- **Header / Personal Info**: Name, title, contact details (email, phone, location), links (LinkedIn, GitHub, Website), summary statement.
- **Experience**: Role, company, location, dates, description, achievements / highlights.
- **Education**: Degree, field of study, institution, location, dates, GPA, highlights.
- **Skills**: Categories, items/lists formatting, grouping tags.
- **Projects**: Name, URL, area, customer, tech stack, description, responsibilities, highlights.
- **Certifications**: Certification name, issuer, date, URL link.
- **Languages**: Language name, proficiency level.
- **Section Visibility & Order**: Verify `config/build.yaml`, `latex/main.tex`, and `web/templates/index.html` maintain identical section order and inclusion rules.

### 3. Apply Synchronization Fixes
- Maintain `data/resume.yaml` as the sole data store.
- Align `scripts/generate_latex.py` and `web/templates/index.html` to parse and render identical keys, lists, and metadata labels.
- Ensure LaTeX escaping (`esc()`) is applied to all dynamic values in `generate_latex.py`.
- Ensure Jinja2 filters (e.g., `replace`, `title`, `join`) in `web/templates/index.html` correctly format nested list structures and strings.
- Keep `latex/styles/resume.sty` and `web/static/css/style.css` aligned in terms of typography hierarchy, accent colors (`#2563EB`), muted text colors (`#6B7280`), and section separator rules.

### 4. Rebuild Outputs
Execute the full clean rebuild pipeline:
```bash
./build_all.sh --clean
./build_all.sh --force
```

### 5. Validate Parity and Consistency
- Verify all section files exist in `latex/sections/*.tex`.
- Verify `output/html/index.html` and `output/pdf/main.pdf` are generated.
- Validate standalone section PDFs in `output/pdf/sections/`.
- Perform semantic checks comparing extracted HTML text with generated LaTeX/PDF sections to ensure no attributes are omitted or formatted inconsistently.

### 6. Reporting
Summarize the findings and changes in the following format:
1. **Discrepancies Found**: Missing keys, mismatched section orders, unhandled types, or formatting divergence.
2. **Files Modified**: List of templates, generator scripts, configs, or style files updated.
3. **Validation Commands & Status**: Build results (`./build_all.sh --force`), exit codes, and output asset verification.
4. **Parity Assessment & Remaining Limitations**: Format-specific constraints (e.g., page-budget vs web scrolling, hyperlinking mechanics) and confirmation of data equivalence.
