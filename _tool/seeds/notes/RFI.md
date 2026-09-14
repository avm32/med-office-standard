---
type: project-rfi
project: "{{PROJECT_CODE}}"
project_name: "{{PROJECT_NAME}}"
tags: [project, rfi]
---

# {{PROJECT_CODE}} {{PROJECT_NAME}} — queries and RFIs

> **This file is yours** — `medstd.py update` never overwrites it.
>
> Questions you are waiting on from someone else. The point is the **waiting**:
> an unanswered question that nobody is tracking becomes an assumption by
> default, and then a problem. When one is answered, it usually becomes either
> a decision ([[{{PROJECT_CODE}}-DECISIONS|DECISIONS]]) or a confirmed
> assumption ([[{{PROJECT_CODE}}-ASSUMPTIONS|ASSUMPTIONS]]) — record it there
> and close the line here.

One line per query. `to` should match a folder in `02-Bejovo` / `08-Kimeno`
so the paper trail and the question line up:

```
- **The question** [to:: Architect] [status:: open] [asked:: YYYY-MM-DD] [via:: email/meeting]
```

`status` values: `open` · `answered` · `dropped`
When answered, add `[answered:: YYYY-MM-DD]` and a one-line summary of the
answer. Do not delete the line.

---

## Open

- **Are the architect's levels SSL or FFL?** [to:: Architect] [status:: open] [asked:: {{DATE}}] [via:: TBC]

## Answered

_Move lines here when answered, with the answer appended._

## Dropped

_Questions overtaken by events. Keep them — they show what was considered._
