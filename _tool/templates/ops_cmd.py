"""medtpl restyle / slim / docs / new.

restyle  push a style fix into an existing document without touching its text
slim     media hygiene on a finished document
docs     regenerate the Hungarian style reference FROM the master
new      start a real document in a project folder
"""

import datetime
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

import build_cmd

TOOL_OWNED = ("word/styles.xml", "word/numbering.xml",
              "word/theme/theme1.xml", "word/fontTable.xml")


# --------------------------------------------------------------------------
# restyle
# --------------------------------------------------------------------------

def read_provenance(path, prop):
    """Return the MEDTPL marker string, or None if this file was not built by us."""
    try:
        with zipfile.ZipFile(path) as zf:
            if "docProps/custom.xml" not in zf.namelist():
                return None
            blob = zf.read("docProps/custom.xml").decode("utf-8", "replace")
    except zipfile.BadZipFile:
        return None
    m = re.search(r'name="%s"[^>]*>\s*<vt:lpwstr>([^<]*)</vt:lpwstr>' % re.escape(prop), blob)
    return m.group(1) if m else None


def cmd_restyle(args, config, medtpl):
    """Replace tool-owned parts in an existing document. Text is untouched.

    Refuses to modify in place any document that lacks the MEDTPL marker, and
    writes <name>.medtpl-new.docx alongside instead. That is the same
    divert-on-foreign-file rule that stops medstd.py clobbering a hand-written
    CLAUDE.md, and it is the single thing that makes this safe to point at a
    live project document.
    """
    target = Path(args.file)
    if not target.is_file():
        sys.exit("error: no such file: %s" % target)

    prop = config["provenance"]["property"]
    marker = read_provenance(target, prop)
    in_place = marker is not None

    master = medtpl.MASTER
    with zipfile.ZipFile(target) as zf:
        parts = {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}

    replaced = []
    for name in TOOL_OWNED:
        src = master / name
        if src.is_file():
            if parts.get(name) != src.read_bytes():
                replaced.append(name)
            parts[name] = src.read_bytes()

    as_template = target.suffix.lower() == ".dotx"
    parts["[Content_Types].xml"] = build_cmd.gen_content_types(
        parts.keys(), as_template, medtpl.TEMPLATE_CT, medtpl.DOCUMENT_CT)

    if in_place:
        out = target
    else:
        out = target.with_suffix(".medtpl-new" + target.suffix)

    if args.dry_run:
        print("[dry run] would %s: %s" % ("update in place" if in_place else "write", out.name))
        print("[dry run]   parts to replace: %s" % (", ".join(replaced) or "none"))
        return 0

    build_cmd.write_package(parts, out, medtpl.FIRST_ENTRY, medtpl.FIXED_DATE)
    if in_place:
        print("restyled in place: %s" % out.name)
        print("  was built by: %s" % marker)
    else:
        print("NOT built by medtpl - left your file untouched.")
        print("  wrote alongside: %s" % out.name)
        print("  Compare the two before replacing anything. A document this tool did")
        print("  not create may rely on styles or direct formatting it knows nothing of.")
    print("  parts replaced: %s" % (", ".join(replaced) or "none - already current"))
    return 0


# --------------------------------------------------------------------------
# slim
# --------------------------------------------------------------------------

def cmd_slim(args, config, medtpl):
    """Media hygiene: drop parts nothing references.

    Note what this does NOT do. Run against the 11.8 MB Hamvas muleiras it
    recovers nothing, because none of that file is orphaned - it is 73
    full-resolution AxisVM screenshots and 8 embedded spreadsheets, all live.
    Bloat like that is an authoring problem (one document holding both the
    muleiras and a 250-page appendix), not something a script can fix.
    """
    target = Path(args.file)
    if not target.is_file():
        sys.exit("error: no such file: %s" % target)

    with zipfile.ZipFile(target) as zf:
        parts = {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}

    # Anything referenced from any .rels file is live.
    referenced = set()
    for name, data in parts.items():
        if name.endswith(".rels"):
            base = str(Path(name).parent.parent).replace("\\", "/").strip(".")
            for tgt in re.findall(r'Target="([^"]+)"', data.decode("utf-8", "replace")):
                if tgt.startswith("http"):
                    continue
                resolved = (base + "/" + tgt).lstrip("/") if base else tgt
                referenced.add(resolved.replace("word/../", ""))

    candidates = [n for n in parts
                  if n.startswith(("word/media/", "word/embeddings/"))]
    orphans = [n for n in candidates if n not in referenced]
    freed = sum(len(parts[n]) for n in orphans)

    print("%s: %d media/embedding parts, %d unreferenced (%s)"
          % (target.name, len(candidates), len(orphans), human(freed)))
    live = sum(len(parts[n]) for n in candidates) - freed
    print("  live media: %s" % human(live))
    if not orphans:
        print("  nothing to recover. If the file is large, the media is all in use -")
        print("  that is an authoring problem, not something slim can solve.")
        return 0
    for n in orphans:
        print("    - %s (%s)" % (n, human(len(parts[n]))))
    if args.dry_run:
        print("[dry run] no changes written")
        return 0
    for n in orphans:
        del parts[n]
    out = target.with_suffix(".slim" + target.suffix)
    build_cmd.write_package(parts, out, medtpl.FIRST_ENTRY, medtpl.FIXED_DATE)
    print("  wrote %s" % out.name)
    return 0


def human(n):
    for unit in ("B", "kB", "MB"):
        if n < 1024 or unit == "MB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


# --------------------------------------------------------------------------
# docs
# --------------------------------------------------------------------------

def cmd_docs(args, config, medtpl):
    """Regenerate the style reference BY READING the master.

    Values are read out of master/word/styles.xml, never asserted here. That is
    the discipline that makes the WG reference trustworthy and is why it is
    worth copying: a hand-maintained reference drifts from the file it claims
    to describe, usually silently.
    """
    from xml.etree import ElementTree as ET
    W = medtpl.W
    master = medtpl.MASTER
    root = ET.fromstring((master / "word/styles.xml").read_bytes())
    styles = {s.get(W + "styleId"): s for s in root.findall(W + "style")}

    def val(el, tag):
        c = el.find(W + tag)
        return c.get(W + "val") if c is not None else ""

    rows = []
    for sid, el in styles.items():
        if el.get(W + "type") != "paragraph":
            continue
        name = val(el, "name")
        if not name or not re.match(r"^\d\d - ", name):
            continue
        ppr = el.find(W + "pPr")
        sp = ppr.find(W + "spacing") if ppr is not None else None
        spacing = ""
        if sp is not None:
            spacing = "line %s %s, before %s, after %s" % (
                sp.get(W + "line") or "-", sp.get(W + "lineRule") or "-",
                sp.get(W + "before") or "0", sp.get(W + "after") or "0")
        rows.append((name, sid, val(el, "basedOn"), val(el, "next"), spacing))
    rows.sort()

    page = config["page"]
    out = medtpl.HERE.parent.parent / "01-Segedletek" / "Word_sablonok.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MED Word sablon — referencia",
        "",
        "> Generálva: `medtpl docs`, %s. Minden érték a `templates/master/word/styles.xml`"
        % datetime.date.today().isoformat(),
        "> fájlból olvasva — **nem újraépítve, nem becsülve.** Kézzel ne szerkeszd:",
        "> módosítsd a mastert, és futtasd újra.",
        "",
        "## Oldalbeállítás",
        "",
        "| | |",
        "|---|---|",
        "| Lapméret | A4 |",
        "| Margók | fent %.1f · lent %.1f · **bal %.1f (fűzés)** · jobb %.1f cm |"
        % (page["margin_top_cm"], page["margin_bottom_cm"],
           page["margin_left_cm"], page["margin_right_cm"]),
        "| Szövegtükör | %.1f cm |" % page["usable_width_cm"],
        "| Betűtípus | %s |" % config["fonts"]["body"],
        "| Nyelv | %s |" % config["language"]["lang"],
        "",
        "A bal oldali fűzőmargó szándékos: a magyar engedélyezési dokumentációt bal",
        "oldalon lefűzve adják be. A WG sablon 5,5 cm-es *jobb* margója az ő",
        "oldalsávjuk — azt nem vettük át.",
        "",
        "## Bekezdésstílusok",
        "",
        "| Stílus | styleId | Alapja | Következő | Térköz |",
        "|---|---|---|---|---|",
    ]
    for name, sid, based, nxt, spacing in rows:
        lines.append("| %s | `%s` | %s | %s | %s |"
                     % (name, sid, based or "—", nxt or "—", spacing or "—"))

    allowed = config["line_spacing_policy"]["exact_allowed"]
    lines += [
        "",
        "## Buktatók",
        "",
        "### Kötött sorköz és a képek",
        "",
        "A `w:lineRule=\"exact\"` rögzíti a sormagasságot, ezért a Word **levágja** a",
        "nála magasabb beillesztett képet. Az `atLeast` ezzel szemben megnöveli a sort —",
        "ez a kettő közti teljes különbség. A WG referencia §5 ezt tévesen írja le",
        "(mindkettőtől óv), és emiatt nem találták meg az olcsó megoldást.",
        "",
        "Ebben a sablonban kötött sorköze **csak** ezeknek a stílusoknak van, ahol a",
        "kötött sormagasság tipográfiai szándék és kép amúgy sem kerül bele:",
        "",
    ] + ["- `%s`" % s for s in allowed] + [
        "",
        "A `medtpl check` ezt a listát ellenőrzi: ha bárhol máshol megjelenik a kötött",
        "sorköz, a build elbukik.",
        "",
        "### Egyéb",
        "",
        "- **Ne gépelj fejezetszámot** a címsor szövegébe. A számozást a",
        "  `numbering.xml` visszahivatkozása adja; ha begépeled, „1 1. Bevezetés” lesz.",
        "- **Ne tegyél képet táblázatcellába** — PDF exportnál eltűnhet. Külön",
        "  bekezdésbe, `15 - Ábra` stílussal.",
        "- A `15 - Ábra` után Enterrel automatikusan a feliratstílusba kerülsz.",
        "",
        "## Tulajdonjog",
        "",
        "A **tartalom** a tiéd (Wordben szerkeszted), a **formázás** a masteré.",
        "Amit begépelsz, túléli az újraépítést; amit kézzel átstílozol, nem —",
        "azt a masterben módosítsd, vagy `medtpl unpack`-kel olvasd vissza.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print("wrote %s (%d styles documented)" % (out, len(rows)))
    return 0


# --------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------

def parse_project_md(path):
    """Pull frontmatter and the facts table out of a project's PROJECT.md."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out = {}
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if fm:
        for line in fm.group(1).splitlines():
            m = re.match(r'^(\w+):\s*"?([^"]*)"?\s*$', line)
            if m:
                out[m.group(1).upper()] = m.group(2).strip()
    for m in re.finditer(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|$", text, re.M):
        key = re.sub(r"\W+", "_", m.group(1).strip()).upper()
        out.setdefault(key, m.group(2).strip())
    return out


# PROJECT.md is written by a person, in Hungarian, with whatever row labels
# suit the project. These map the labels actually seen onto the tokens the
# layout uses, so the file stays natural to write.
FACT_ALIASES = {
    "SEISMIC": "SEISMIC",
    "STOREY_ARRANGEMENT": "BUILDING_CHARACTER",
    "SZINTEK": "BUILDING_CHARACTER",
    "ÉPÜLET_JELLEMZŐI": "BUILDING_CHARACTER",
    "BUILDING_TYPE": "BUILDING_TYPE",
    "ÉPÍTÉSI_TEVÉKENYSÉG": "BUILDING_TYPE",
    "HELYRAJZI_SZÁM": "HRSZ",
    "HELYRAJZI_SZAM": "HRSZ",
    "HRSZ.": "HRSZ",
    "TERVEZŐ": "DESIGNER",
    "TERVEZO": "DESIGNER",
    "KAMARAI_NÉVJEGYZÉK_SZÁMA": "CHAMBER_NUMBER",
    "KAMARAI_SZÁM": "CHAMBER_NUMBER",
    "CHAMBER_NUMBER": "CHAMBER_NUMBER",
    "MEGBÍZÓ": "CLIENT",
    "ÉPÍTÉSZ": "ARCHITECT",
    "ARCHITECT": "ARCHITECT",
    "CÍM": "ADDRESS",
}


def apply_aliases(facts):
    for src, dest in FACT_ALIASES.items():
        if src in facts and not facts.get(dest):
            facts[dest] = facts[src]
    # "162163 (telek 797 m2)" -> "162163": the parenthetical is a site note,
    # not part of the land registry number that goes on the cover.
    hrsz = facts.get("HRSZ", "")
    if hrsz:
        facts["HRSZ"] = re.split(r"[\s(]", hrsz.strip(), 1)[0].rstrip(".,")
    return facts


LAYOUT_DESCRIPTIONS = {
    "statikai-muleiras": "Engterv_statikai_muleiras",
}

# Where each layout files itself inside the project. The design stage lives in
# the folder because the container ID has no field for it.
LAYOUT_SUBFOLDER = {
    "statikai-muleiras": "01-Engterv",
}


def layout_description(layout):
    return LAYOUT_DESCRIPTIONS.get(layout, "")


def slugify_desc(text):
    """ASCII, underscore-separated. The description is human help, not an
    identifier - it must never contain a hyphen, which is the field delimiter."""
    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def cmd_new(args, config, medtpl):
    """Start a real document in a project folder, named per the container ID."""
    project = Path(args.project)
    if not project.is_dir():
        sys.exit("error: not a project folder: %s" % project)

    notes = project / "00-Notes"
    code = project.name.split("-")[0]
    facts = {}
    if notes.is_dir():
        for cand in notes.glob("*-PROJECT.md"):
            facts = apply_aliases(parse_project_md(cand))
            break

    today = datetime.date.today()
    hu_months = ["január", "február", "március", "április", "május", "június",
                 "július", "augusztus", "szeptember", "október", "november", "december"]
    tokens = {
        "PROJECT_CODE": facts.get("PROJECT_CODE", code),
        "PROJECT_NAME": facts.get("NAME") or facts.get("PROJECT_NAME", ""),
        "CLIENT": facts.get("CLIENT", "TBC"),
        "ADDRESS": facts.get("ADDRESS", "TBC"),
        "HRSZ": facts.get("HRSZ", "TBC"),
        "DESIGNER": args.designer or facts.get("DESIGNER", "TBC"),
        "CHAMBER_NUMBER": args.chamber or facts.get("CHAMBER_NUMBER", "TBC"),
        "PRACTICE_ADDRESS": config.get("practice_address", "TBC"),
        "PLACE": args.place or "Budapest",
        "DATE_HU": "%d. %s %d." % (today.year, hu_months[today.month - 1], today.day),
        "REVISION": args.revision or "S3-P01",
        "ARCHITECT": facts.get("ARCHITECT", facts.get("ÉPÍTÉSZ", "TBC")),
        "BUILDING_TYPE": facts.get("BUILDING_TYPE", "TBC"),
        "BUILDING_TYPE_LOWER": facts.get("BUILDING_TYPE", "TBC").lower(),
        "BUILDING_CHARACTER": facts.get("BUILDING_CHARACTER", "TBC"),
        # Seismic basis: stated in the muleiras because DCL vs DCM decides
        # whether ductile detailing rules apply at all.
        "AGR": facts.get("AGR", "TBC"),
        "GROUND_TYPE": facts.get("GROUND_TYPE", "TBC"),
        "DUCTILITY_CLASS": facts.get("DUCTILITY_CLASS", "TBC"),
        "Q_FACTOR": facts.get("Q_FACTOR", "TBC"),
        "DESIGNER_INITIALS": "".join(w[0] for w in
            (args.designer or facts.get("DESIGNER", "")).split() if w)[:3].upper() or "—",
        "VERSION": config["tool_version"],
        "DATE": today.isoformat(),
    }

    # Container ID per the office standard: Project-Originator-Functional-
    # Spatial-Form-Discipline-Number, with status and revision suffixed.
    #
    # ISO 19650 has NO design-stage field, deliberately - stage is a property of
    # the issue, not of the document. So the stage shows up two other ways:
    #   1. the folder it lives in (01-Engedelyezesi_terv)
    #   2. an optional description suffix after the ID, which is what BS 1192
    #      allowed via an underscore and what survives a file being emailed out
    #      of its folder.
    # The ID itself stays fixed-field and parseable either way.
    base = "%s-MED-ZZ-ZZ-T-S-0001-%s" % (tokens["PROJECT_CODE"], tokens["REVISION"])
    desc = args.description if args.description is not None else layout_description(args.layout)
    name = base + (("_" + slugify_desc(desc)) if desc else "") + ".docx"
    sub = LAYOUT_SUBFOLDER.get(args.layout, "")
    dest_dir = project / args.into / sub if sub else project / args.into
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not dest_dir.is_dir():
        sys.exit("error: destination folder does not exist: %s\n"
                 "  (pass --into with the right folder for this project's language)" % dest_dir)
    out = dest_dir / name
    if out.exists() and not args.force:
        sys.exit("error: %s already exists. Refusing to overwrite a live document." % out)

    build_cmd.build_layout(args.layout, config, medtpl, tokens=tokens,
                           out_override=str(out), force_content=True)
    print("created %s" % out)
    missing = [k for k, v in tokens.items() if v == "TBC"]
    if missing:
        print("  still TBC: %s" % ", ".join(sorted(missing)))
        print("  fill these into %s-PROJECT.md rather than typing them into the document -"
              % tokens["PROJECT_CODE"])
        print("  then they populate every document from one place.")
    return 0
