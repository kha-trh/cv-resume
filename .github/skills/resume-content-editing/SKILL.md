---
name: resume-content-editing
description: "Use when: updating resume content in data/resume.yaml, rewriting experience bullets, fixing summary text, or adjusting personal/project/education details. Focuses on content structure and formatting rules for this data-driven resume project."
---

# Resume Content Editing

Use this skill for content-only changes to the resume. The repository is intentionally data-driven: most work belongs in [data/resume.yaml](../../../data/resume.yaml), not in generated LaTeX or HTML output.

## Core rules

- Edit [data/resume.yaml](../../../data/resume.yaml) as the single source of truth.
- Do not hand-edit files under [latex/sections](../../../latex/sections) or generated outputs under [output](../../../output).
- Keep YAML structure valid. Preserve the correct nesting for each section.
- If a section should be hidden, disable it in [config/build.yaml](../../../config/build.yaml) rather than deleting the generator.
- After content edits, regenerate output with the smallest relevant build command.

## Expected schema

The resume content follows these top-level keys:

- `personal`
- `experience`
- `education`
- `skills`
- `projects`
- `certifications`
- `languages`

Each section has a known shape:

### personal
- `name`, `title`, `email`, `phone`, `location`, `linkedin`, `summary`

### experience
- list of objects with `company`, `role`, `location`, `start`, `end`, `achievements`

### education
- list of objects with `institution`, `degree`, `field`, `location`, `start`, `end`, `gpa`, `highlights`

### skills
- mapping of skill categories to arrays, for example `languages`, `frameworks`, `databases`, `tools`

### projects
- list of objects with `name`, `url`, `area`, `customer`, `description`, `tech`, `responsibilities`, `highlights`

### certifications
- list of objects with `name`, `issuer`, `date`, `url`

### languages
- list of objects with `language`, `proficiency`

## Editing guidance

- Prefer plain, concise professional wording in bullet points.
- Keep lists consistent: short phrases or sentence fragments are fine for highlights.
- Preserve valid YAML quoting when values contain colons, apostrophes, or commas.
- For URLs, use the real value; the template and generator will render them as links.
- Keep the content factually accurate, especially for dates, institutions, and role names.
- If a field is intentionally blank, use `None` or leave the entry empty only if the upstream generator handles it correctly.

## Build validation

After editing resume content, validate with the smallest relevant build:

```bash
./build_all.sh --tex
./build_all.sh --html
./build_all.sh --pdf
```

For a full rebuild:

```bash
./build_all.sh
```

## Common mistakes to avoid

- Editing generated files in [latex/sections](../../../latex/sections)
- Reformatting template files instead of the YAML data
- Removing a top-level section without updating the generator expectations
- Adding new YAML keys without checking whether the HTML template needs them
- Mixing Markdown or HTML into fields that are intended for plain text or LaTeX-safe strings

## Default workflow

1. Update the relevant entries in [data/resume.yaml](../../../data/resume.yaml).
2. Keep the YAML structure aligned with the project schema.
3. Run the smallest build needed to verify the output.
4. Inspect the generated files in [output/pdf](../../../output/pdf) and [output/html](../../../output/html) only as validation, not as editing targets.
