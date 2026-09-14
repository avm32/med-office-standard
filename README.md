# MED Office Standard

Folder structure, file naming and per-project agent setup for
**Medek Mernoki Iroda kft**.

One repository, one source of truth: [`standard.json`](standard.json). Everything
else is generated from it or consumes it.

```
standard.json          the standard, as data. Edit this.
medstd.py              the tool. Creates and maintains project folders.
seeds/                 files copied into every project, with {{TOKEN}} substitution
docs/OFFICE-STANDARD.md  human-readable standard, generated
projects.csv           project register, appended by `medstd.py new`
```

## Use

```bash
# create a new project (English folder names)
python medstd.py new 26014 "Szemlohegy utca" --client "..." --address "..."

# Hungarian folder names
python medstd.py new 26015 "Bartok Bela ut" --lang hu

# see what would happen, change nothing
python medstd.py new 26016 "Test" --dry-run

# bring an existing project up to the current standard (safe, idempotent)
python medstd.py update "../../02-Projects/26014-Szemlohegy_utca"

# regenerate the readable standard after editing standard.json
python medstd.py docs

# report files that do not follow the naming convention
python medstd.py check "../../02-Projects/26014-Szemlohegy_utca"
```

Requires Python 3.7+. **No third-party packages** — that is deliberate, so the
tool still runs years from now without a working `pip`.

## The two properties that matter

**Idempotent.** Every command creates what is missing and touches nothing else.
Run `update` on a project as often as you like. This is what lets the standard
evolve: change `standard.json`, then `update` each live project to pick up new
folders and refreshed agent files.

**Managed vs. yours.** `medstd.py update` regenerates `CLAUDE.md` and
`OFFICE-STANDARD.md` in each project, because those derive from the standard. It
never touches `PROJECT.md`, `DECISIONS.md` or `REGISTER.csv`, because those
accumulate your content. If you need a project-specific instruction for the
agent, put it in `PROJECT.md`, not `CLAUDE.md` — otherwise the next `update`
will overwrite it.

## Language

Folder names come in English or Hungarian, chosen per project with `--lang`, and
recorded in `PROJECT.md`. Hungarian names are deliberately **ASCII-folded**
(`Szamitasok`, not `Számítások`): accented characters in paths cause trouble in
CAD tools, ZIP archives, and cross-platform sync, and Windows path-length limits
bite sooner. `medstd.py update` auto-detects an existing project's language from
its folder names, so you never have to remember which one a job used.

## Per-project agent

Each project gets a `CLAUDE.md`, so opening the project folder with Claude Code
gives you an assistant that already knows the office standard, the naming
convention, where things go, and the jurisdiction hierarchy. Supporting files:

| File | Managed? | Purpose |
|------|----------|---------|
| `CLAUDE.md` | generated | agent instructions — role, hard rules, standing tasks |
| `OFFICE-STANDARD.md` | generated | the code tables, so the agent needs no lookup |
| `.claude/commands/` | generated | project slash commands — `/decision` |
| `PROJECT.md` | yours | client, address, stage, design basis, team, project codes |
| `DECISIONS.md` | yours | append-only decision log — the project wiki |
| `REGISTER.csv` | yours | issue register, one row per file per issue |

**`/decision`** writes a formatted entry into `DECISIONS.md`, inferring the
reasoning from the session and asking for it when it can't. Nothing watches your
files — the log only captures what passes through a session, so use the command
when something is settled. Edit the command at
`seeds/dotclaude/commands/decision.md`, not in a project.

To migrate a project that has already started, see
[`01-Segedletek/Projekt_migracio.md`](01-Segedletek/Projekt_migracio.md).

The technical knowledge base stays central at `03-Resources-Wiki/` — it is not
copied per project.

## Conventions

- Folders are numbered (`01-`, `02-`, … `XX-`) so they sort predictably and can
  be referred to by number in conversation.
- Folders that represent **events rather than categories** take a date prefix
  instead: `260910-Design_Team_Meeting`. This applies inside `01-Admin/05-Meetings`,
  `02-Incoming/*`, `08-Outgoing` and `XX-Superseded`.
- `XX-` is reserved for superseded and out-of-scope content, matching the
  convention already used in `03-Resources-Wiki`.
- Calculations are filed **by subject, not by work stage**. Stage snapshots are
  frozen into `08-Outgoing` instead.

## Note on git inside OneDrive

This repository lives in OneDrive, which is convenient but means the sync client
watches `.git/`. For a single-user repository this is normally fine. Two things
reduce the risk:

- Don't run long git operations while OneDrive is mid-sync.
- Push to a remote (private GitHub) so the history exists somewhere that is not
  a synced folder.

If it ever misbehaves, move the working copy to a local path outside OneDrive and
treat the remote as the source of truth.
