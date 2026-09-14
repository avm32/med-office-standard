---
description: Log or confirm an assumption in ASSUMPTIONS.md
---

Record an assumption in `{{NOTES_LINK}}/{{PROJECT_CODE}}-ASSUMPTIONS.md`.

What is assumed (or what is being confirmed): $ARGUMENTS

An assumption is something the design **currently relies on that has not been
confirmed**. It is a debt, not a decision. If it is settled, it belongs in
`{{PROJECT_CODE}}-DECISIONS.md` via `/decision` instead — say so and stop.

Steps:

1. Read the file. Decide whether `$ARGUMENTS` describes a **new** assumption or
   **confirms an existing one**.
2. **Confirming an existing one:** change its `[status:: assumed]` to
   `[status:: confirmed]`, append `[confirmed:: YYYY-MM-DD]` and `[by:: source]`,
   and move the line to the `## Confirmed` section. **Never delete the line** —
   the record of what was believed, and when, is the point.
   If it turned out wrong, use `[status:: superseded]` and the `## Superseded`
   section instead, and check whether any decision in
   `{{PROJECT_CODE}}-DECISIONS.md` rested on it. Say which, if so.
3. **New assumption:** append to `## Open` in exactly this shape, keeping every
   inline field — they are what make it findable from the vault dashboard:

```
- **What is assumed** [status:: assumed] [basis:: why] [affects:: what] [raised:: YYYY-MM-DD]
```

4. `basis` must say why it is currently reasonable ("engineering judgement
   pending GI", "architect's email 26-09-08"). `affects` names the calculation,
   drawing or element that would change if it turned out wrong. If you cannot
   determine `affects` from the session, ask — an assumption whose blast radius
   is unknown is the dangerous kind.

Use today's date. Then show the line you wrote or changed, and nothing else.

If `$ARGUMENTS` is empty, review the session and `{{PROJECT_CODE}}-PROJECT.md`
for anything marked TBC or relied on without confirmation, and propose entries
before writing.

<!-- Managed by medstd.py. Edit seeds/dotclaude/commands/assumption.md in the
     office standard repo, not this copy — this one is regenerated on update. -->
