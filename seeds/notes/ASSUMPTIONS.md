---
type: project-assumptions
project: "{{PROJECT_CODE}}"
project_name: "{{PROJECT_NAME}}"
tags: [project, assumptions]
---

# {{PROJECT_CODE}} {{PROJECT_NAME}} — assumptions

> **This file is yours** — `medstd.py update` never overwrites it.
>
> An assumption is something the design currently relies on that has **not been
> confirmed**. Distinct from a decision: a decision is settled, an assumption is
> a debt. These are what hurt when they are forgotten.
>
> Every assumption is either `assumed`, `confirmed` or `superseded`. Nothing
> gets deleted — a superseded assumption is evidence of what you believed and
> when.

Each line is one assumption. The `[key:: value]` fields are Dataview inline
fields — they are what make an assumption findable from the vault dashboard,
so keep them on every entry:

```
- **What is assumed** [status:: assumed] [basis:: why] [affects:: what] [raised:: YYYY-MM-DD]
```

`status` values: `assumed` · `confirmed` · `superseded`
When one is confirmed, change the status and add `[confirmed:: YYYY-MM-DD]` and
`[by:: source]` — do not delete the line.

---

## Open

- **Allowable bearing capacity 150 kPa** [status:: assumed] [basis:: engineering judgement pending ground investigation] [affects:: 04-Szamitasok/02-Alapozas] [raised:: {{DATE}}]
- **Consequence class CC2** [status:: assumed] [basis:: standard residential, EN 1990 Table B1] [affects:: all partial factors] [raised:: {{DATE}}]
- **Hungarian National Annex governs** [status:: assumed] [basis:: project location] [affects:: all NDPs] [raised:: {{DATE}}]

## Confirmed

_Move lines here when confirmed. Keep the original wording, change the status._

## Superseded

_Assumptions that turned out wrong. Keep them — they explain earlier decisions._
