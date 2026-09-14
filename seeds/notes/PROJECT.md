---
type: project
code: "{{PROJECT_CODE}}"
name: "{{PROJECT_NAME}}"
client: "{{CLIENT}}"
address: "{{ADDRESS}}"
status: live
stage: "{{STAGE}}"
language: {{LANG}}
originator: {{ORIGINATOR}}
national_annex: HU
consequence_class: CC2
opened: {{DATE}}
files: "{{PROJECT_PATH}}"
tags: [project]
---

# {{PROJECT_CODE}} — {{PROJECT_NAME}}

> Project facts. **This file is yours** — `medstd.py update` never overwrites it.
> Fill it in at project start; the agent reads it first.
>
> `Hrsz.`, `Designer` and `Chamber number` are read by `medtpl new` when it
> generates a műleírás, so fill them here rather than typing them into each
> document.
>
> Companions: [[{{PROJECT_CODE}}-ASSUMPTIONS|assumptions]] · [[{{PROJECT_CODE}}-DECISIONS|decisions]] · [[{{PROJECT_CODE}}-RFI|queries]]
>
> Project files live at `{{PROJECT_PATH}}` — this note deliberately does not.
> Keeping it in the wiki vault is what lets one Obsidian query span every
> project and the knowledge base at once.

| | |
|---|---|
| **Project code** | {{PROJECT_CODE}} |
| **Name** | {{PROJECT_NAME}} |
| **Client** | {{CLIENT}} |
| **Address** | {{ADDRESS}} |
| **Hrsz.** | TBC |
| **Stage** | {{STAGE}} |
| **Originator** | {{ORIGINATOR}} |
| **Folder language** | {{LANG}} |
| **Opened** | {{DATE}} |
| **Designer** | TBC |
| **Chamber number** | TBC |

## Scope

_What we are appointed to do, and explicitly what we are not._

## Design basis

| | |
|---|---|
| **Codes** | EN 1990–1998 |
| **National Annex** | Hungarian NA _(confirm — Swiss/SIA or British if the project requires)_ |
| **Consequence class** | CC2 _(confirm)_ |
| **Design working life** | 50 years _(confirm)_ |
| **Exposure / durability** | _TBC_ |
| **Fire resistance** | _TBC_ |
| **Seismic** | _EN 1998 + HU NA — confirm whether it governs_ |
| **Ground conditions** | _TBC — see 03-Site_Information_ |
| **Assumed bearing capacity** | _TBC_ |

> Anything left as _TBC_ belongs in [[{{PROJECT_CODE}}-ASSUMPTIONS|ASSUMPTIONS]]
> as a tracked line, not just as a gap here. The agent should flag it when it
> becomes load-bearing on a calculation.

## Project team

| Role | Organisation | Contact | Originator code |
|------|--------------|---------|-----------------|
| Client | {{CLIENT}} | | K |
| Architect | | | A |
| Structural | {{PRACTICE}} | | {{ORIGINATOR}} |
| Mechanical | | | M |
| Electrical | | | E |
| Geotechnical | | | G |
| Contractor | | | W |

## Project-specific codes

Beyond the office standard. Any addition here must be agreed before use.

**Functional breakdown**

| Code | Meaning |
|------|---------|
| `ZZ` | Multiple subdivisions |
| `SB` | Substructure |
| `SS` | Superstructure |

**Spatial breakdown**

| Code | Meaning |
|------|---------|
| `ZZ` | Multiple levels |
| `00` | Ground floor |

## Key constraints

_Site, planning, party wall, access, programme, budget._

## Open items

- [ ] Confirm National Annex
- [ ] Confirm consequence class
- [ ] Obtain ground investigation
