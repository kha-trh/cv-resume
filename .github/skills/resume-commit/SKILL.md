---
name: resume-commit
description: "Use when: creating a Git commit message for this resume repository, reviewing staged changes for a commit, or preparing a commit from .gitmessage.txt."
---

# Resume Commit

Create a Conventional Commits-style message using the repository template in [.gitmessage.txt](../../../.gitmessage.txt).

## Workflow

1. Inspect the repository state with `git status --short`.
2. Review the staged diff first with `git diff --cached`. If nothing is staged, review `git diff` and clearly state that the proposed message is based on unstaged changes.
3. Read [.gitmessage.txt](../../../.gitmessage.txt) and follow its commit types, subject format, body guidance, and footer guidance.
4. Choose the most accurate type from the template. Use a concise lowercase scope when one area is clearly affected, such as `data`, `latex`, `build`, or `docs`. Omit the scope when the change spans unrelated areas.
5. Write a subject in the form `type(scope): short summary` or `type: short summary`, with a maximum length of 72 characters. Use imperative mood and do not end the subject with a period.
6. Add a body only when the diff needs motivation or context. Wrap body lines at 72 characters.
7. Present the proposed complete commit message in a fenced `gitcommit` block and briefly summarize the changes it covers.
8. Do not run `git commit` unless the user explicitly asks to commit after reviewing the proposed message.

## Repository-specific guidance

- Resume content changes belong in [data/resume.yaml](../../../data/resume.yaml); generated files under `latex/sections` and `output` should normally not be committed unless the repository workflow explicitly requires generated assets.
- Do not include unrelated working-tree changes in the proposed message.
- Do not invent issue references, breaking changes, or motivation that are not supported by the diff.
- If the staged diff contains multiple independent changes, recommend separate commits rather than forcing them into one message.

## Output format

Return:

```gitcommit
type(scope): short summary

Optional body explaining why the change was made.
```

Then include one short sentence identifying the files or behavior covered by the message.
