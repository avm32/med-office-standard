---
description: Log or close a query in RFI.md
---

Record a query in `{{NOTES_LINK}}/{{PROJECT_CODE}}-RFI.md`.

The question, or the answer received: $ARGUMENTS

Steps:

1. Read the file. Decide whether `$ARGUMENTS` is a **new question** or an
   **answer to one already open**.
2. **New question:** append to `## Open`, keeping every inline field:

```
- **The question** [to:: Architect] [status:: open] [asked:: YYYY-MM-DD] [via:: email]
```

   `to` must match a party folder in `02-Bejovo` / `08-Kimeno` so the question
   and the paper trail line up. Use the English party name.

3. **Answer received:** change `[status:: open]` to `[status:: answered]`, append
   `[answered:: YYYY-MM-DD]` and a one-line summary of the answer, and move the
   line to `## Answered`. **Never delete it.**

   Then carry the outcome onward, and say which you did:
   - if it settles something, log it with the decision format in
     `{{PROJECT_CODE}}-DECISIONS.md`
   - if it confirms an assumption, update that line in
     `{{PROJECT_CODE}}-ASSUMPTIONS.md` to `[status:: confirmed]`

   An answer that lands nowhere but this file will be lost.

4. If a question has gone unanswered long enough that the design has moved on,
   it has quietly become an assumption. Say so and offer to add it to
   `{{PROJECT_CODE}}-ASSUMPTIONS.md`.

Use today's date. Then show the line you wrote or changed, and nothing else.

If `$ARGUMENTS` is empty, list the open queries with how long they have been
open, oldest first.

<!-- Managed by medstd.py. Edit seeds/dotclaude/commands/rfi.md in the
     office standard repo, not this copy — this one is regenerated on update. -->
