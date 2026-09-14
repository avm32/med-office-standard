---
description: Log a decision to DECISIONS.md
---

Log a decision to `{{NOTES_LINK}}/{{PROJECT_CODE}}-DECISIONS.md`.

What was decided: $ARGUMENTS

Steps:

1. Read `{{NOTES_LINK}}/{{PROJECT_CODE}}-DECISIONS.md`. If the same decision is already logged, update that
   entry rather than adding a duplicate — say which entry you updated.
2. Work out the four fields below from `$ARGUMENTS` plus the current session.
   You have the conversation in front of you: pull the reasoning, the source
   and the affected documents from it rather than asking about things you can
   already see.
3. **If the *why* is not recoverable from the arguments or the session, ask for
   it before writing.** A decision without its reasoning is close to worthless
   six months later — that one line is the whole point of the log. Everything
   else you may reasonably infer, marking an inference as such.
4. Insert the entry **immediately below the `---` separator**, above any
   existing entries. Newest first. Never rewrite or reorder existing entries.

Format exactly:

```
## [YYYY-MM-DD] Short title
- **Decision:** what was decided
- **Why:** the reasoning, and what was rejected
- **Basis:** source, clause, email, meeting, or "engineering judgement"
- **Affects:** which drawings, calcs or parties
```

Use today's date. Keep the title short enough to scan in a list.

Where the decision rests on a code clause or a concept that has a page in
the knowledge base, link it as `[[EC7_1_BS_EN_1997]]` or `[[Punching_Shear]]`.
The backlink is what makes that wiki page show every project that used it.

Then show the entry you wrote, and nothing else — no preamble, no summary of
the file.

If `$ARGUMENTS` is empty, look back over this session for anything that was
settled and is not yet in the log, and propose entries for confirmation before
writing.

<!-- Managed by medstd.py. Edit seeds/dotclaude/commands/decision.md in the
     office standard repo, not this copy — this one is regenerated on update. -->

