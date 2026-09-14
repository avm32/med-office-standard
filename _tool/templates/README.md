# MED Word templates

Hungarian Word templates for **Medek Mérnöki Iroda Kft.**, built from a style
master under version control.

The one rule: **content goes in Word, formatting goes in `master/`.** What you
type into a built document survives a rebuild. What you restyle by hand does
not — change `master/`, or `unpack` your change back into it.

```
medtpl.py          the tool (stdlib only)
templates.json     policy: page setup, fonts, the exact-spacing allowlist, ownership
master/            THE SOURCE OF TRUTH - XML parts, diffable
layouts/           declarative document skeletons
assets/            logo
derive/            the one-shot WG -> Hungarian transform, kept for provenance
build/             outputs (gitignored)
```

## Commands

```bash
python medtpl.py check                  # 11 structural checks, exit 1 on failure
python medtpl.py roundtrip              # assert pack -> unpack is byte-identical
python medtpl.py build                  # build every layout
python medtpl.py build stiluskatalogus  # just one
python medtpl.py docs                   # regenerate 01-Segedletek/Word_sablonok.md
python medtpl.py unpack <file.docx> --yes   # capture Word edits back into master/
python medtpl.py restyle <file.docx>    # push a style fix into an existing document
python medtpl.py slim <file.docx>       # report / drop unreferenced media
python medtpl.py new <project-folder>   # start a real műleírás in a project
```

Then verify in Word, which is the only thing that can tell you the file is
genuinely valid:

```bash
powershell -File verify_word.ps1 -Doc build/MED-Statikai_muleiras.dotx -Pdf
```

## Why master/ is a directory, not a .docx

Generating `styles.xml` from scratch means reproducing `docDefaults`, 369
latent style entries, theme linkage and numbering geometry correctly from
nothing — each a place Word silently misbehaves or offers to repair the file,
with no error saying which. Keeping a pristine binary master avoids that but
makes every style change an unreviewable binary diff.

So `master/` is the *exploded* package. Parts that provably carry no text
(`styles.xml`, `numbering.xml`, `settings.xml`, `fontTable.xml`, `theme1.xml`)
are pretty-printed one element per line and diff properly; text-bearing parts
are byte-verbatim. `roundtrip` asserts `pack → unpack` reproduces every part
byte-identically, which is what makes the tree trustworthy.

The loop closes through Word: hand-finish a built file, `unpack` it, `git diff`
shows exactly what Word changed, commit or revert.

## The image-clipping fix

`w:lineRule="exact"` pins the line box, so Word **clips** any inline image
taller than it. `atLeast` grows the box instead — that is the entire
difference. The WG reference advises against both, which is why the cheap fix
was never found there.

`Normal` now uses `atLeast`. Fixed spacing survives only where a fixed box is
the typographic point and an image would be a user error anyway — chapter
titles and the caption style. That set is listed in `templates.json` and
**`medtpl check` asserts it exactly**, so an edit that reintroduces the trap
fails the build.

Verified by measurement, not assertion: a 400pt image in a `Normal` paragraph
renders full height here and clips to one line in the WG original.

## Style naming

Word identifies built-in styles by their canonical English `w:name` and
localises the *display* name per UI language. You therefore **cannot** give a
built-in a Hungarian name — rewriting it converts the style into an
unrecognised custom one and breaks whatever auto-applies it.

- **Word applies it automatically → stays built-in, retuned only.** `Normal`,
  `caption`, `header`, `footer`, `toc 1-3`, `Table Grid`.
- **You pick it from the gallery → custom, Hungarian name, ASCII styleId.**
  `11 - Szöveg`, `21 - Címsor 1`, `15 - Ábra`, `48 - Aláírás` …

The numbered prefix is load-bearing, not decoration: on a Hungarian Word the
built-in heading displays as `Címsor 1`, and a custom style with that exact
name would collide. `21 - Címsor 1` cannot, in any UI language.

`Heading 1-9` remain defined but `semiHidden`, so the custom headings are what
people see. TOC, the Navigation pane and PDF bookmarks read `w:outlineLvl`, not
the style name, so they work regardless.

## Traps worth knowing

Each of these cost real debugging time and is now covered by a check:

- **OOXML content models are strict sequences.** `<w:semiHidden/>` after
  `<w:pPr>` makes Word reject the entire file with only *"the file appears to
  be corrupted"*.
- **A duplicate `PartName` in `[Content_Types].xml`** does the same.
- **Relationship ids are per-part.** An `r:embed` in `header1.xml` resolves
  against `word/_rels/header1.xml.rels`, never `document.xml.rels`. Get it
  wrong and the file opens fine but the image does not render.
- **`numbering.xml` carries bullet glyphs in Symbol, Wingdings and Courier
  New.** A blanket font retarget turns every bullet into a letter.
- **PowerShell variables are case-insensitive**, so a local `$doc` silently
  clobbers a `-Doc` parameter.
- **PowerShell 5.1 reads `.ps1` as ANSI without a UTF-8 BOM**, mangling every
  accented style name.

## Live documents

`restyle` refuses to modify in place any document lacking the `MEDTPL`
provenance property, writing `<name>.medtpl-new.docx` alongside instead. So it
is safe to point at a real project file — the 11.8 MB Hamvas műleírás, for
instance, is left untouched and a restyled copy appears next to it to compare.

`slim` only removes media nothing references. Run against that same file it
recovers nothing, because none of it is orphaned: it is 73 full-resolution
AxisVM screenshots and 8 embedded spreadsheets. Bloat like that is an authoring
problem — one document holding both the műleírás and a 250-page appendix — not
something a script can fix.
