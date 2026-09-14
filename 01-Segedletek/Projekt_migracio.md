# Migrating an existing project onto the standard

For a job that has already started and has real content in it.

`medstd.py update` **adds** the standard structure. It does not move your files
into it — it cannot guess where they belong, and guessing wrong with real project
data is worse than doing nothing. So migration is: run the tool, then move
content in deliberately.

Budget 20 minutes for a project a few weeks old.

---

## Before you start

**The safety net is OneDrive version history**, not the tool. OneDrive keeps
previous versions and a Recycle Bin for deleted items, so a mis-drag is
recoverable — right-click the folder → *Version history*. Know that this exists
before you start moving things.

The tool itself never deletes, moves or renames anything. The only files it will
overwrite are ones it wrote itself, and only when they still carry its
generation marker.

---

## 1. Choose a project code

`YYNNN` — two-digit year, three-digit sequence. `26014` is the 14th job started
in 2026. Check `projects.csv` in the office standard folder for the last number
used.

The code goes in every filename this project ever issues, so decide it once and
do not change it.

## 2. Rename the project folder

```
02-Projects/Szemlohegy utca/    →    02-Projects/26014-Szemlohegy_utca/
```

Code, hyphen, then the name with underscores and no accents. Do this before
running the tool so the tool can read the code and name back off the folder.

## 3. Run update

```bash
cd "01-Admin/10-Office_Standard"

# look first — writes nothing
python medstd.py update "../../02-Projects/26014-Szemlohegy_utca" --dry-run

# then for real
python medstd.py update "../../02-Projects/26014-Szemlohegy_utca" \
    --lang en \
    --client "..." \
    --address "..." \
    --stage "Concept"
```

You now have the standard tree sitting alongside your existing content, plus
`PROJECT.md`, `DECISIONS.md`, `REGISTER.csv`, `CLAUDE.md`, `OFFICE-STANDARD.md`
and a `.claude/commands/` folder.

Use `--lang hu` for Hungarian folder names. Decide once per project; `update`
auto-detects it from then on.

## 4. Move your content in

By hand, in Explorer. Typical moves:

| What you have | Where it goes |
|---|---|
| Anything a consultant or the client sent you | `02-Incoming/<party>/YYMMDD-Description/` |
| Survey, ground investigation, existing drawings | `03-Site_Information/` |
| Sizing spreadsheets, hand calcs, analysis output | `04-Calculations/<subject>/` |
| Robot / AxisVM / SOFiSTiK / Rhino / Revit files | `05-Models/` |
| Live CAD files, sketches | `06-Drawings/` |
| Reports, specs, schedules | `07-Documents/` |
| PDFs you have already sent out | `08-Outgoing/YYMMDD-<status>-<purpose>/` |
| Anything already replaced | `XX-Superseded/YYMMDD-Reason/` |

Two rules that save pain later:

- **Do not retro-rename historical files.** Files already issued keep the names
  they were issued under — that is what the recipient has. The naming convention
  starts from today, on the next thing you issue. A project with a clean break
  is easy to explain; one that has been half-renamed is not.
- **If you genuinely cannot tell where something goes**, it is probably
  `01-Admin/04-Correspondence` or `02-Incoming/08-Other`. Do not invent a folder.

Empty folders you never use can be deleted. `update` recreates them, so if you
want them gone permanently, remove them from `standard.json` instead.

## 5. Fill in PROJECT.md

The 10 minutes with the highest payoff. The agent reads this first, every
session — client, address, stage, National Annex, consequence class, design
life, ground assumptions, project team.

Anything left as *TBC* is a live assumption. That is the point of leaving it
visible: the agent flags it when it becomes load-bearing on a calculation.

## 6. Record the migration

```bash
claude
> /decision migrated onto the office standard
```

First entry in the decision log, and a check that the agent is wired up.

---

## Using it day to day

Open a terminal in the project folder and run `claude`. It reads `CLAUDE.md`,
`PROJECT.md` and `OFFICE-STANDARD.md` automatically — roughly 4k tokens, so
there is no reason to be sparing with sessions.

Things worth asking it:

```
what's in the architect's latest issue, and what changes for us?
draft a load take-off for the second floor
give me the container ID for the ground floor GA
create the issue folder for today's client review
/decision grid moved 600mm east to clear the drainage run
what's still TBC in PROJECT.md?
```

**Filing incoming.** Give it the file. It proposes a destination and waits for
your confirmation before moving anything — that is deliberate, per its
instructions.

**Issuing.** Ask it to create the issue folder. It makes
`08-Outgoing/YYMMDD-<status>-<purpose>/`, renames copies to the full container
ID with status and revision, appends to `REGISTER.csv` and drafts the
transmittal.

**Calculations.** It drafts; you check. Everything it produces is marked `S0`
work in progress and states its assumptions. That is a liability boundary, not
false modesty — do not let it drift.

**The decision log only captures what passes through a session.** Nothing
watches your files. Get into the habit of `/decision` when something is settled,
and of asking *"anything worth logging?"* before you close a session.

---

## Checking it stuck

```bash
python medstd.py check "../../02-Projects/26014-Szemlohegy_utca"
```

Reports files under `08-Outgoing` that do not parse as container IDs, or that
use codes not in the standard. Expect noise on a migrated project — historical
files predate the convention. Run it on what you issue from now on.

## When the standard changes

Edit `standard.json`, then:

```bash
python medstd.py docs                      # regenerate the readable standard
python medstd.py update <each live project>  # pick up new folders and agent files
```

Safe to run as often as you like. It adds what is missing and leaves your
`PROJECT.md`, `DECISIONS.md` and `REGISTER.csv` alone.
