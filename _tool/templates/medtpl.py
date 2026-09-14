#!/usr/bin/env python3
"""MED Word template tool.

Builds and maintains Word templates from an exploded master under version
control. Stdlib only - no third-party packages - so it still runs in ten years
without a working pip. (derive/derive.py is the exception: it uses lxml, runs
once, and is then dormant.)

    medtpl.py pack                     master/ -> a .docx
    medtpl.py pack --template          master/ -> a .dotx
    medtpl.py unpack <file.docx>       a .docx -> master/ (capture Word edits)
    medtpl.py check                    the automated battery; exit 1 on failure
    medtpl.py roundtrip                assert pack->unpack is byte-identical

The ownership rule: content goes in Word, formatting goes in master/. What you
type into a built document survives a rebuild; what you restyle by hand does
not - change master/, or unpack your change back into it.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
CONFIG_FILE = HERE / "templates.json"
MASTER = HERE / "master"
BUILD = HERE.parent.parent / "02-Sablonok"   # where a person looks for them

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Word is picky about this being the first entry in the package.
FIRST_ENTRY = "[Content_Types].xml"
# A fixed timestamp makes pack reproducible - otherwise every build produces a
# different zip and "did anything actually change?" becomes unanswerable.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)

TEMPLATE_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"
DOCUMENT_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"

# ECMA-376 CT_Style and CT_PPrBase child sequences. Kept in step with the same
# lists in derive/derive.py - one writes in this order, the other asserts it.
STYLE_ORDER = [
    "name", "aliases", "basedOn", "next", "link", "autoRedefine", "hidden",
    "uiPriority", "semiHidden", "unhideWhenUsed", "qFormat", "locked",
    "personal", "personalCompose", "personalReply", "rsid",
    "pPr", "rPr", "tblPr", "trPr", "tcPr", "tblStylePr",
]
PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
    "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
    "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
    "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr",
    "pPrChange",
]


def load_config():
    try:
        with CONFIG_FILE.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit("error: templates.json not found next to medtpl.py")
    except json.JSONDecodeError as exc:
        sys.exit("error: templates.json is not valid JSON\n  line %d, column %d: %s"
                 % (exc.lineno, exc.colno, exc.msg))


# --------------------------------------------------------------------------
# pretty printing
# --------------------------------------------------------------------------

def pretty_xml(data):
    """Indent an XML part one element per line, textually.

    Deliberately does NOT parse and re-serialise. Round-tripping OOXML through
    stdlib ElementTree rewrites namespace prefixes (w: becomes ns0:), which Word
    tolerates unevenly and which makes diffs useless. Scanning the text instead
    preserves every byte except the whitespace between tags.

    Only valid for parts with no text content - the caller must guarantee that,
    and `unpack` asserts it.
    """
    text = data.decode("utf-8")
    tokens = []
    i, n = 0, len(text)
    while i < n:
        lt = text.find("<", i)
        if lt < 0:
            tokens.append(("text", text[i:]))
            break
        if lt > i:
            tokens.append(("text", text[i:lt]))
        # scan to the closing '>', respecting quoted attribute values
        j, quote = lt + 1, None
        while j < n:
            ch = text[j]
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == ">":
                break
            j += 1
        tokens.append(("tag", text[lt:j + 1]))
        i = j + 1

    out, depth = [], 0
    for kind, tok in tokens:
        if kind == "text":
            if tok.strip():
                raise ValueError("pretty_xml called on a part with text content: %r"
                                 % tok.strip()[:40])
            continue
        if tok.startswith("<?") or tok.startswith("<!"):
            out.append(tok)
            continue
        if tok.startswith("</"):
            depth -= 1
            out.append("  " * depth + tok)
        elif tok.endswith("/>"):
            out.append("  " * depth + tok)
        else:
            out.append("  " * depth + tok)
            depth += 1
    return ("\n".join(out) + "\n").encode("utf-8")


def has_text_content(data):
    """True if the part carries any non-whitespace text between tags."""
    text = data.decode("utf-8", "replace")
    return bool(re.search(r">\s*[^<\s][^<]*<", text))


# --------------------------------------------------------------------------
# pack / unpack
# --------------------------------------------------------------------------

def part_paths(root):
    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and p.name != "MANIFEST.json"
    )


def pack(master, out_path, as_template=False, config=None):
    parts = part_paths(master)
    if FIRST_ENTRY not in parts:
        sys.exit("error: %s missing from %s" % (FIRST_ENTRY, master))
    ordered = [FIRST_ENTRY] + [p for p in parts if p != FIRST_ENTRY]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for part in ordered:
            data = (master / part).read_bytes()
            if part == FIRST_ENTRY:
                data = set_main_content_type(data, as_template)
            info = zipfile.ZipInfo(part, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, data)
    return out_path, len(ordered)


def set_main_content_type(data, as_template):
    """Switch /word/document.xml between the document and template content types.

    This is the only thing that makes a .dotx a .dotx. It also means python-docx
    cannot read the result - it hard-fails on the template content type - so a
    .dotx is a terminal output and every read/write stage works on .docx.
    """
    text = data.decode("utf-8")
    want = TEMPLATE_CT if as_template else DOCUMENT_CT
    other = DOCUMENT_CT if as_template else TEMPLATE_CT
    return text.replace(other, want).encode("utf-8")


def unpack(src, into, config, quiet=False):
    pretty_set = set(config["xml_format"]["pretty_print"])
    into.mkdir(parents=True, exist_ok=True)
    for child in sorted(into.rglob("*"), key=lambda p: -len(p.parts)):
        if child.name == "MANIFEST.json":
            continue
        try:
            child.unlink() if child.is_file() else child.rmdir()
        except OSError:
            pass  # OneDrive keeps handles on synced folders

    written = []
    with zipfile.ZipFile(src) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            data = zf.read(name)
            if name in pretty_set:
                if has_text_content(data):
                    sys.exit("error: %s is on the pretty-print list but carries text "
                             "content.\n  Refusing to reformat it - that would change "
                             "what the document says." % name)
                data = pretty_xml(data)
            dest = into / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            written.append(name)
    write_manifest(into, config)
    if not quiet:
        print("unpacked %d parts into %s" % (len(written), into))
    return written


def write_manifest(root, config):
    pretty_set = set(config["xml_format"]["pretty_print"])
    manifest = {"_note": "Hashes let `medtpl check` detect hand edits to master/.",
                "parts": {}}
    for part in part_paths(root):
        data = (root / part).read_bytes()
        manifest["parts"][part] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "format": "pretty" if part in pretty_set else "verbatim",
        }
    (root / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def parse_part(root, name):
    path = root / name
    if not path.is_file():
        return None
    return ET.fromstring(path.read_bytes())


def effective_spacing(styles, sid, attr, _seen=None):
    """Resolve a spacing attribute up the basedOn chain."""
    _seen = _seen or set()
    if sid in _seen or sid not in styles:
        return None
    _seen.add(sid)
    el = styles[sid]
    ppr = el.find(W + "pPr")
    if ppr is not None:
        sp = ppr.find(W + "spacing")
        if sp is not None and sp.get(W + attr) is not None:
            return sp.get(W + attr)
    based = el.find(W + "basedOn")
    if based is not None:
        return effective_spacing(styles, based.get(W + "val"), attr, _seen)
    return None


def check(root, config, verbose=True):
    problems, checks = [], []

    def ok(label):
        checks.append(("ok", label))

    def fail(label, detail):
        checks.append(("FAIL", label))
        problems.append("%s: %s" % (label, detail))

    styles_root = parse_part(root, "word/styles.xml")
    if styles_root is None:
        return ["word/styles.xml missing"], checks
    styles = {s.get(W + "styleId"): s for s in styles_root.findall(W + "style")}

    # 1. duplicate ids and names
    ids = [s.get(W + "styleId") for s in styles_root.findall(W + "style")]
    dupes = {i for i in ids if ids.count(i) > 1}
    names = []
    for s in styles_root.findall(W + "style"):
        nm = s.find(W + "name")
        if nm is not None:
            names.append(nm.get(W + "val"))
    dupe_names = {n for n in names if names.count(n) > 1}
    if dupes or dupe_names:
        fail("unique style ids and names", "duplicate ids %s, names %s" % (dupes, dupe_names))
    else:
        ok("unique style ids and names (%d styles)" % len(ids))

    # 2. basedOn / next graph resolves, no cycles
    dangling = []
    for sid, el in styles.items():
        for tag in ("basedOn", "next", "link"):
            ref = el.find(W + tag)
            if ref is not None and ref.get(W + "val") not in styles:
                dangling.append("%s.%s -> %s" % (sid, tag, ref.get(W + "val")))
    cycles = []
    for sid in styles:
        seen, cur = set(), sid
        while cur in styles:
            if cur in seen:
                cycles.append(sid)
                break
            seen.add(cur)
            b = styles[cur].find(W + "basedOn")
            cur = b.get(W + "val") if b is not None else None
    if dangling or cycles:
        fail("style graph", "dangling %s; cycles %s" % (dangling[:5], cycles[:5]))
    else:
        ok("style graph: no dangling basedOn/next/link, no cycles")

    # 3. every style reference in every part resolves
    unresolved = []
    for part in part_paths(root):
        if not part.endswith(".xml"):
            continue
        try:
            el_root = ET.fromstring((root / part).read_bytes())
        except ET.ParseError as exc:
            fail("xml well-formed", "%s: %s" % (part, exc))
            continue
        for tag in ("pStyle", "rStyle", "tblStyle"):
            for el in el_root.iter(W + tag):
                val = el.get(W + "val")
                if val and val not in styles:
                    unresolved.append("%s -> %s" % (part, val))
    if unresolved:
        fail("style references resolve", "; ".join(sorted(set(unresolved))[:6]))
    else:
        ok("every pStyle/rStyle/tblStyle resolves")

    # 4. numbering references resolve
    num_root = parse_part(root, "word/numbering.xml")
    if num_root is not None:
        nums = {n.get(W + "numId") for n in num_root.findall(W + "num")}
        abstracts = {a.get(W + "abstractNumId") for a in num_root.findall(W + "abstractNum")}
        bad = []
        for n in num_root.findall(W + "num"):
            ref = n.find(W + "abstractNumId")
            if ref is not None and ref.get(W + "val") not in abstracts:
                bad.append("num %s -> abstract %s" % (n.get(W + "numId"), ref.get(W + "val")))
        missing_style = []
        for el in num_root.iter(W + "pStyle"):
            if el.get(W + "val") not in styles:
                missing_style.append(el.get(W + "val"))
        if bad or missing_style:
            fail("numbering resolves", "%s %s" % (bad[:4], sorted(set(missing_style))[:4]))
        else:
            ok("numbering: %d nums -> %d abstracts, back-links resolve"
               % (len(nums), len(abstracts)))

    # 5. THE REGRESSION TEST: effective exact line spacing matches the allowlist
    allowed = set(config["line_spacing_policy"]["exact_allowed"])
    actual = set()
    for sid in styles:
        if styles[sid].get(W + "type") != "paragraph":
            continue
        if effective_spacing(styles, sid, "lineRule") == "exact":
            actual.add(sid)
    if actual != allowed:
        fail("image-clipping regression test",
             "styles with exact line spacing changed.\n"
             "      unexpected: %s\n"
             "      missing:    %s"
             % (sorted(actual - allowed) or "none", sorted(allowed - actual) or "none"))
    else:
        ok("image-clipping regression: exact spacing confined to %d allowed styles"
           % len(allowed))

    # 6. schema element order
    # OOXML content models are strict sequences. A child in the wrong position
    # makes Word reject the entire file with "the file appears to be corrupted"
    # and no clue which element is at fault - so this is checked here rather
    # than discovered in Word.
    out_of_order = []
    for sid, el in styles.items():
        for parent, order in ((el, STYLE_ORDER),
                              (el.find(W + "pPr"), PPR_ORDER)):
            if parent is None:
                continue
            ranks, names = [], []
            for child in parent:
                name = child.tag.split("}")[-1]
                if name in order:
                    ranks.append(order.index(name))
                    names.append(name)
            for i in range(1, len(ranks)):
                if ranks[i] < ranks[i - 1]:
                    out_of_order.append("%s: <%s> after <%s>" % (sid, names[i], names[i - 1]))
                    break
    if out_of_order:
        fail("schema element order", "; ".join(out_of_order[:6]))
    else:
        ok("schema element order correct in every style")

    # 7. forbidden content
    found = []
    for part in part_paths(root):
        blob = (root / part).read_bytes().decode("utf-8", "replace")
        for bad in config["strip"]["forbidden_substrings"]:
            if bad in blob:
                found.append("%s in %s" % (bad, part))
    if found:
        fail("forbidden content", "; ".join(found[:6]))
    else:
        ok("no Frutiger, de-CH/de-DE, or WG marks")

    # 7. fonts limited to the whitelist
    whitelist = set(config["fonts"]["whitelist"])
    seen_fonts = set()
    for part in ("word/styles.xml", "word/numbering.xml", "word/fontTable.xml"):
        el_root = parse_part(root, part)
        if el_root is None:
            continue
        # Only w:rFonts and w:font carry typeface names. Scanning every element
        # for an eastAsia attribute also picks up w:lang's, which made this
        # report "hu-HU" as a missing font.
        for el in el_root.iter(W + "rFonts"):
            for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
                v = el.get(W + attr)
                if v:
                    seen_fonts.add(v)
        for el in el_root.iter(W + "font"):
            if el.get(W + "name"):
                seen_fonts.add(el.get(W + "name"))
    stray = seen_fonts - whitelist
    if stray:
        fail("font whitelist", "not confirmed present on office machines: %s" % sorted(stray))
    else:
        ok("fonts within whitelist: %s" % ", ".join(sorted(seen_fonts)))

    # 8. content types: every part declared exactly once, nothing undeclared
    ct = parse_part(root, FIRST_ENTRY)
    if ct is not None:
        CTNS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
        overrides = [o.get("PartName") for o in ct.findall(CTNS + "Override")]
        defaults = {d.get("Extension").lower() for d in ct.findall(CTNS + "Default")}
        dupe_ct = sorted({p for p in overrides if overrides.count(p) > 1})
        undeclared = []
        for part in part_paths(root):
            if part == FIRST_ENTRY:
                continue
            ext = part.rsplit(".", 1)[-1].lower()
            if "/" + part not in overrides and ext not in defaults:
                undeclared.append(part)
        if dupe_ct or undeclared:
            fail("content types",
                 "duplicate overrides %s; undeclared parts %s" % (dupe_ct, undeclared[:4]))
        else:
            ok("content types: %d overrides, each part declared once" % len(overrides))

    # 9. no unsubstituted tokens
    # A literal {{TOKEN}} means a value never got filled and shipped as braces.
    # Table cells were emitted raw for a while and leaked six of them.
    leaks = []
    for part in part_paths(root):
        if not part.endswith(".xml"):
            continue
        blob = (root / part).read_bytes().decode("utf-8", "replace")
        for tok in set(re.findall(r"\{\{[A-Z_]+\}\}", blob)):
            leaks.append("%s in %s" % (tok, part))
    if leaks:
        fail("no unsubstituted tokens", "; ".join(sorted(leaks)[:6]))
    else:
        ok("no unsubstituted {{TOKEN}} left in any part")

    # 10. relationships resolve
    rel_problems = []
    for rels_path in root.rglob("*.rels"):
        rel_root = ET.fromstring(rels_path.read_bytes())
        base = rels_path.parent.parent
        for rel in rel_root:
            target = rel.get("Target")
            if rel.get("TargetMode") == "External" or target is None:
                continue
            resolved = (base / target).resolve()
            if not resolved.is_file():
                rel_problems.append("%s -> %s" % (rels_path.name, target))
    if rel_problems:
        fail("relationship targets exist", "; ".join(rel_problems[:6]))
    else:
        ok("every relationship target exists")

    # 11. per-part relationship ids resolve
    # Relationship ids are scoped to the part that uses them: an r:embed inside
    # header1.xml resolves against word/_rels/header1.xml.rels, never against
    # document.xml.rels. Declaring it in the wrong place still opens in Word -
    # the image simply does not render - so nothing else here would catch it.
    dangling_ids = []
    for part in part_paths(root):
        if not part.endswith(".xml") or "/_rels/" in part or part == FIRST_ENTRY:
            continue
        blob = (root / part).read_bytes().decode("utf-8", "replace")
        used = set(re.findall(r'r:(?:id|embed|link)="(rId\d+)"', blob))
        if not used:
            continue
        rels_path = root / Path(part).parent / "_rels" / (Path(part).name + ".rels")
        declared = set()
        if rels_path.is_file():
            declared = set(re.findall(r'Id="(rId\d+)"',
                                      rels_path.read_bytes().decode("utf-8", "replace")))
        missing = used - declared
        if missing:
            dangling_ids.append("%s uses %s, declared: %s"
                                % (part, sorted(missing), sorted(declared) or "none"))
    if dangling_ids:
        fail("per-part relationship ids", "; ".join(dangling_ids[:4]))
    else:
        ok("per-part relationship ids resolve")

    if verbose:
        for status, label in checks:
            print("  %-5s %s" % (status, label))
    return problems, checks


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_pack(args, config):
    out = Path(args.out) if args.out else BUILD / ("MED-master.dotx" if args.template
                                                   else "MED-master.docx")
    path, n = pack(MASTER, out, args.template, config)
    print("packed %d parts -> %s (%s)" % (n, path, "template" if args.template else "document"))
    return 0


def cmd_unpack(args, config):
    src = Path(args.file)
    if not src.is_file():
        sys.exit("error: no such file: %s" % src)
    into = Path(args.into) if args.into else MASTER
    if into == MASTER and not args.yes:
        print("This overwrites master/ with the contents of %s." % src.name)
        print("That is the intended way to capture hand edits made in Word - but")
        print("review `git diff` afterwards before committing.")
        print("Re-run with --yes to proceed.")
        return 1
    unpack(src, into, config)
    return 0


def cmd_check(args, config):
    target = Path(args.target) if args.target else MASTER
    if target.is_file():
        tmp = HERE / ".medtpl-check"
        unpack(target, tmp, config, quiet=True)
        target = tmp
    print("checking %s" % target)
    problems, checks = check(target, config)
    print()
    if problems:
        print("%d problem(s):" % len(problems))
        for p in problems:
            print("  ! %s" % p)
        return 1
    print("all %d checks passed" % len(checks))
    return 0


def cmd_roundtrip(args, config):
    """pack -> unpack -> compare. The assertion that makes the exploded tree
    trustworthy: if it does not hold, master/ is not a faithful representation
    of the document and every diff below it is suspect."""
    tmp_zip = HERE / ".medtpl-rt.docx"
    tmp_dir = HERE / ".medtpl-rt"
    pack(MASTER, tmp_zip, False, config)
    unpack(tmp_zip, tmp_dir, config, quiet=True)

    before = {p: (MASTER / p).read_bytes() for p in part_paths(MASTER)}
    after = {p: (tmp_dir / p).read_bytes() for p in part_paths(tmp_dir)}
    problems = []
    for part in sorted(set(before) | set(after)):
        if part not in before:
            problems.append("appeared: %s" % part)
        elif part not in after:
            problems.append("vanished: %s" % part)
        elif before[part] != after[part]:
            problems.append("differs: %s (%d -> %d bytes)"
                            % (part, len(before[part]), len(after[part])))
    tmp_zip.unlink(missing_ok=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    if problems:
        print("round-trip FAILED - master/ is not faithful:")
        for p in problems:
            print("  ! %s" % p)
        return 1
    print("round-trip clean: pack -> unpack reproduces all %d parts byte-identically"
          % len(before))
    return 0


def main(argv=None):
    config = load_config()
    ap = argparse.ArgumentParser(prog="medtpl", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = ap.add_subparsers(dest="cmd", required=True)

    sp = subs.add_parser("pack", help="master/ -> a .docx or .dotx")
    sp.add_argument("--template", action="store_true", help="write a .dotx")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_pack)

    sp = subs.add_parser("unpack", help="a .docx -> master/ (capture Word edits)")
    sp.add_argument("file")
    sp.add_argument("--into")
    sp.add_argument("--yes", action="store_true")
    sp.set_defaults(func=cmd_unpack)

    sp = subs.add_parser("check", help="the automated battery")
    sp.add_argument("target", nargs="?")
    sp.set_defaults(func=cmd_check)

    sp = subs.add_parser("build", help="master/ + layout -> build/")
    sp.add_argument("layout", nargs="?", help="layout name; omit to build all")
    sp.add_argument("--out")
    sp.add_argument("--force-content", action="store_true",
                    help="regenerate document.xml even if the target exists "
                         "(DISCARDS hand edits made in Word)")
    sp.set_defaults(func=lambda a, c: __import__("build_cmd").cmd_build(a, c, sys.modules[__name__]))

    sp = subs.add_parser("roundtrip", help="assert pack->unpack is byte-identical")
    sp.set_defaults(func=cmd_roundtrip)

    me = sys.modules[__name__]
    ops = lambda fn: (lambda a, c: getattr(__import__("ops_cmd"), fn)(a, c, me))

    sp = subs.add_parser("restyle", help="push a style fix into an existing document")
    sp.add_argument("file")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--remap", action="store_true",
                    help="rewrite style references when Word has regenerated the ids")
    sp.set_defaults(func=ops("cmd_restyle"))

    sp = subs.add_parser("slim", help="report and drop unreferenced media")
    sp.add_argument("file")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=ops("cmd_slim"))

    sp = subs.add_parser("docs", help="regenerate the Hungarian style reference")
    sp.set_defaults(func=ops("cmd_docs"))

    sp = subs.add_parser("new", help="start a real document in a project folder")
    sp.add_argument("project", help="the project folder")
    sp.add_argument("--layout", default="statikai-muleiras")
    sp.add_argument("--into", default="07-Dokumentumok/02-Muszaki_Leiras",
                    help="destination inside the project (Hungarian folder names by default)")
    sp.add_argument("--designer")
    sp.add_argument("--chamber", help="chamber / nevjegyzeki number")
    sp.add_argument("--place")
    sp.add_argument("--revision")
    sp.add_argument("--description", help="human-readable suffix after the ID; "
                                          "pass \"\" for none")
    sp.add_argument("--signature", help="signature image in assets/ to embed")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=ops("cmd_new"))

    args = ap.parse_args(argv)
    return args.func(args, config)


if __name__ == "__main__":
    sys.exit(main())
