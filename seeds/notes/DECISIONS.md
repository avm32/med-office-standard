---
type: project-decisions
project: "{{PROJECT_CODE}}"
project_name: "{{PROJECT_NAME}}"
tags: [project, decisions]
---

# {{PROJECT_CODE}} {{PROJECT_NAME}} — decision log

> The project wiki. Append-only, **newest first**. This file is yours —
> `medstd.py update` never overwrites it.
>
> Log anything a future reader would otherwise have to re-derive: a scheme
> choice, a load assumption, a client instruction, a departure from the office
> standard, a contradiction between consultants. If you find yourself
> explaining a decision twice, it belongs here.

Format:

```
## [YYYY-MM-DD] Short title
- **Decision:** what was decided
- **Why:** the reasoning, and what was rejected
- **Basis:** source, clause, email, meeting
- **Affects:** which drawings, calcs or parties
```

Link out where it helps. `[[EC7_1_BS_EN_1997]]` or `[[Punching_Shear]]`
reaches the knowledge base, and the backlink means that wiki page then shows
every project that leaned on it — which is the whole reason these notes live
in the vault rather than in the project folder.

---

## [{{DATE}}] Project opened
- **Decision:** Folder structure created to the {{PRACTICE}} office standard, language `{{LANG}}`.
- **Why:** Standard structure and naming from day one; retrofitting is expensive.
- **Basis:** `01-Admin/10-Office_Standard/`
- **Affects:** all project files
