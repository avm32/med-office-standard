"""medtpl build: master/ + a layout JSON -> a built .docx / .dotx.

Transplant, not regeneration. If the target already exists, only tool-owned
parts are replaced; document.xml, the headers, the footers and any media you
added are carried through untouched. That is what lets a template be
hand-finished in Word and still pick up a later style fix.
"""

import datetime
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import render

REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

# Parts the user owns once a document exists. On rebuild these are preserved
# from the target rather than regenerated.
# A kept part's relationships must be kept with it. word/_rels/header1.xml.rels
# does not start with "word/header", so leaving it out silently produced a
# header with no relationships and an unresolvable logo.
USER_PREFIXES = ("word/document.xml", "word/header", "word/footer",
                 "word/media/", "word/embeddings/",
                 "word/_rels/header", "word/_rels/footer",
                 "word/_rels/document.xml.rels")

BASE_RELS = [
    ("rId1", "styles", "styles.xml"),
    ("rId2", "numbering", "numbering.xml"),
    ("rId3", "settings", "settings.xml"),
    ("rId4", "webSettings", "webSettings.xml"),
    ("rId5", "fontTable", "fontTable.xml"),
    ("rId6", "theme", "theme/theme1.xml"),
    ("rId7", "endnotes", "endnotes.xml"),
    ("rId8", "footnotes", "footnotes.xml"),
    ("rId10", "header", "header1.xml"),
    ("rId11", "footer", "footer1.xml"),
]


def gen_rels(rels):
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Relationships xmlns="%s">' % PR_NS]
    for rid, typ, target in rels:
        lines.append('  <Relationship Id="%s" Type="%s%s" Target="%s"/>'
                     % (rid, REL_BASE, typ, target))
    lines.append("</Relationships>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def gen_content_types(parts, as_template, template_ct, document_ct):
    o = "application/vnd.openxmlformats-officedocument.wordprocessingml."
    kinds = {
        "word/document.xml": template_ct if as_template else document_ct,
        "word/styles.xml": o + "styles+xml",
        "word/numbering.xml": o + "numbering+xml",
        "word/settings.xml": o + "settings+xml",
        "word/webSettings.xml": o + "webSettings+xml",
        "word/fontTable.xml": o + "fontTable+xml",
        "word/endnotes.xml": o + "endnotes+xml",
        "word/footnotes.xml": o + "footnotes+xml",
        "word/theme/theme1.xml": "application/vnd.openxmlformats-officedocument.theme+xml",
        "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "docProps/app.xml":
            "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        "docProps/custom.xml":
            "application/vnd.openxmlformats-officedocument.custom-properties+xml",
    }
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Types xmlns="%s">' % CT_NS,
             '  <Default Extension="rels" '
             'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
             '  <Default Extension="xml" ContentType="application/xml"/>',
             '  <Default Extension="png" ContentType="image/png"/>',
             '  <Default Extension="jpg" ContentType="image/jpeg"/>',
             '  <Default Extension="jpeg" ContentType="image/jpeg"/>',
             '  <Default Extension="svg" ContentType="image/svg+xml"/>']
    # sorted(set(...)): a duplicate PartName override is invalid OOXML and Word
    # rejects the whole package with only "the file appears to be corrupted".
    for part in sorted(set(parts)):
        ct = kinds.get(part)
        if ct is None and part.startswith("word/header"):
            ct = o + "header+xml"
        elif ct is None and part.startswith("word/footer"):
            ct = o + "footer+xml"
        if ct:
            lines.append('  <Override PartName="/%s" ContentType="%s"/>' % (part, ct))
    lines.append("</Types>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def gen_custom_props(config, layout_name, master_dir, part_paths, docprops):
    """docProps/custom.xml: the MEDTPL provenance marker plus the project data
    that DOCPROPERTY fields read.

    Values repeated across cover, nyilatkozat and footer live here once. Edit
    them in Word via File > Info > Properties > Advanced, then Ctrl+A / F9 to
    refresh every instance.
    """
    master_hash = hashlib.sha256(
        b"".join((master_dir / p).read_bytes() for p in part_paths(master_dir))
    ).hexdigest()[:16]
    marker = "medtpl %s; layout=%s; master=%s; built=%s" % (
        config["tool_version"], layout_name, master_hash,
        datetime.date.today().isoformat())

    ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    props = [(config["provenance"]["property"], marker)]
    props += sorted(docprops.items())

    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Properties xmlns="%s" xmlns:vt="%s">' % (ns, vt)]
    for i, (name, val) in enumerate(props, start=2):
        safe = (str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        lines.append('  <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" '
                     'pid="%d" name="%s"><vt:lpwstr>%s</vt:lpwstr></property>'
                     % (i, name, safe))
    lines.append("</Properties>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def gen_provenance(config, layout_name, master_dir, part_paths):
    """The MEDTPL marker - parallel to medstd.py's GENERATED_MARKER.

    `restyle` refuses to modify in place any document lacking it, which is the
    single rule that makes this tool safe to point at a live project file.
    """
    master_hash = hashlib.sha256(
        b"".join((master_dir / p).read_bytes() for p in part_paths(master_dir))
    ).hexdigest()[:16]
    val = "medtpl %s; layout=%s; master=%s; built=%s" % (
        config["tool_version"], layout_name, master_hash,
        datetime.date.today().isoformat())
    ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Properties xmlns="%s" xmlns:vt="%s">\n'
            '  <property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="%s">'
            '<vt:lpwstr>%s</vt:lpwstr></property>\n'
            '</Properties>\n' % (ns, vt, config["provenance"]["property"], val)).encode("utf-8")


def write_package(parts, out_path, first_entry, fixed_date):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = [first_entry] + [p for p in sorted(parts) if p != first_entry]
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for part in ordered:
            info = zipfile.ZipInfo(part, date_time=fixed_date)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zf.writestr(info, parts[part])


def build_layout(name, config, medtpl, tokens=None, out_override=None,
                 force_content=False):
    spec = config["layouts"].get(name)
    if spec is None:
        sys.exit("error: unknown layout %r. Known: %s"
                 % (name, ", ".join(sorted(config["layouts"]))))

    here = medtpl.HERE
    master = medtpl.MASTER
    layout = json.loads((here / spec["file"]).read_text(encoding="utf-8"))
    out = Path(out_override) if out_override else medtpl.BUILD / spec["out"]
    as_template = out.suffix.lower() == ".dotx"

    parts = {p: (master / p).read_bytes() for p in medtpl.part_paths(master)}

    kept = {}
    if out.exists() and not force_content:
        with zipfile.ZipFile(out) as zf:
            for n in zf.namelist():
                if n.startswith(USER_PREFIXES):
                    kept[n] = zf.read(n)

    ctx = render.Ctx(tokens=tokens or {})
    ctx["logo_h_cm"] = layout.get("logo_h_cm", 1.6)
    ctx["logo_w_cm"] = layout.get("logo_w_cm", ctx["logo_h_cm"])
    ctx["header_rel"] = "rId10"
    ctx["footer_rel"] = "rId11"

    rels = list(BASE_RELS)
    logo = layout.get("logo")
    header_rels = None
    if logo:
        src = here / logo
        if not src.is_file():
            sys.exit("error: layout logo not found: %s" % src)
        media = "word/media/medtpl-logo" + src.suffix.lower()
        parts[media] = src.read_bytes()
        target = media.split("word/", 1)[1]

        # Relationship ids are PER PART. An r:embed inside header1.xml resolves
        # against word/_rels/header1.xml.rels, never against document.xml.rels -
        # declaring it only in the latter leaves the header image unresolvable.
        ctx["logo_rel"] = "rId20"          # used by body images (document.xml)
        ctx["logo_rel_header"] = "rId1"    # used by the header part
        rels.append(("rId20", "image", target))
        header_rel_list = [("rId1", "image", target)]

        # Vector logo, if one sits beside the raster. Word 2016+ renders the
        # SVG; the raster stays as the mandatory fallback.
        svg_src = src.with_suffix(".svg")
        if svg_src.is_file():
            svg_media = "word/media/medtpl-logo.svg"
            parts[svg_media] = svg_src.read_bytes()
            svg_target = svg_media.split("word/", 1)[1]
            ctx["logo_svg_rel"] = "rId21"
            ctx["logo_svg_rel_header"] = "rId2"
            rels.append(("rId21", "image", svg_target))
            header_rel_list.append(("rId2", "image", svg_target))
        header_rels = gen_rels(header_rel_list)

    # Resolved before rendering: a DOCPROPERTY field caches its value as the
    # field result, so the values must be known while the document is built.
    docprops = {}
    for key, spec in (layout.get("docprops") or {}).items():
        if key.startswith("_"):
            continue
        docprops[key] = render.substitute(str(spec), ctx)
    ctx["docprops"] = docprops

    if kept:
        parts.update(kept)
    else:
        parts["word/document.xml"] = render.render_document(layout, config, ctx)
        parts["word/header1.xml"] = render.render_header(
            ctx, with_logo=bool(logo), right_text=layout.get("header_right", ""),
            lines=layout.get("header_lines"))
        if header_rels:
            parts["word/_rels/header1.xml.rels"] = header_rels
        if layout.get("footer_lines"):
            parts["word/footer1.xml"] = render.render_footer_lines(
                ctx, layout["footer_lines"])
        else:
            parts["word/footer1.xml"] = render.render_footer(
                ctx, left_text=layout.get("footer_left", ""))

    parts["word/_rels/document.xml.rels"] = gen_rels(rels)
    parts["[Content_Types].xml"] = gen_content_types(
        parts.keys(), as_template, medtpl.TEMPLATE_CT, medtpl.DOCUMENT_CT)
    parts["docProps/custom.xml"] = gen_custom_props(
        config, name, master, medtpl.part_paths, docprops)

    write_package(parts, out, medtpl.FIRST_ENTRY, medtpl.FIXED_DATE)
    return out, len(parts), len(kept), as_template


def cmd_build(args, config, medtpl):
    names = [args.layout] if args.layout else sorted(config["layouts"])
    for name in names:
        out, n, kept, as_tpl = build_layout(
            name, config, medtpl, out_override=args.out,
            force_content=args.force_content)
        how = ("kept %d content parts from the existing file (your Word edits)" % kept
               if kept else "generated content from the layout")
        print("built %-20s -> %s%s" % (name, out.name, "  [template]" if as_tpl else ""))
        print("      %d parts, %s" % (n, how))
    return 0
