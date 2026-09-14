#!/usr/bin/env python3
"""One-shot derivation: WaltGalmarini master -> Medek Hungarian master.

Run ONCE. Its output is templates/master/, which is thereafter the source of
truth; this script then lies dormant. It is kept committed so the provenance of
every style value has an answer.

    python derive/derive.py                 # writes master/
    python derive/derive.py --dry-run
    python derive/derive.py --force         # overwrite an existing master/

Uses lxml, unlike medtpl.py. That is deliberate and contained: this runs once,
on a developer machine, while medtpl.py must still work in ten years without a
working pip.

The style parts (styles, numbering, settings, fontTable, theme) are carried over
from WG and transformed. document.xml, the headers and the footers are generated
fresh rather than inherited - inheriting them would drag in the WG wordmark and
leave dangling relationships once it was stripped.
"""

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent
MAP_FILE = HERE / "wg_to_hu.json"
CONFIG_FILE = TEMPLATES / "templates.json"
MASTER = TEMPLATES / "master"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
w = lambda tag: "{%s}%s" % (W, tag)
r_ = lambda tag: "{%s}%s" % (R, tag)

# Parts carried over from the WG master and transformed.
CARRY = [
    "word/styles.xml",
    "word/numbering.xml",
    "word/settings.xml",
    "word/fontTable.xml",
    "word/theme/theme1.xml",
    "word/webSettings.xml",
    "word/endnotes.xml",
    "word/footnotes.xml",
]

# Every place a styleId can be referenced. Renaming is a graph edit: miss one of
# these and Word silently drops the formatting rather than reporting an error.
STYLE_REFS = [
    (w("basedOn"), w("val")),
    (w("next"), w("val")),
    (w("link"), w("val")),
    (w("styleLink"), w("val")),
    (w("numStyleLink"), w("val")),
    (w("pStyle"), w("val")),
    (w("rStyle"), w("val")),
    (w("tblStyle"), w("val")),
    (w("clickAndTypeStyle"), w("val")),
]

CM = 567.0  # twips per cm
A4_W, A4_H = 11906, 16838

# Fonts that must survive the retarget. numbering.xml uses these to carry the
# actual bullet glyphs - a blanket swap to Arial turns every bullet into a
# letter. Discovered the hard way by the forbidden-content sweep.
SYMBOL_FONTS = {
    "Symbol", "Wingdings", "Wingdings 2", "Wingdings 3", "Webdings",
    "Courier New", "Times New Roman",
}


def load(path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse(data):
    return etree.fromstring(data)


def serialise(el, declaration=True):
    return etree.tostring(el, xml_declaration=declaration, encoding="UTF-8", standalone=True)


# --------------------------------------------------------------------------
# styles.xml
# --------------------------------------------------------------------------

# OOXML content models are strict SEQUENCES, not bags: a child in the wrong
# position makes Word reject the whole file with "the file appears to be
# corrupted" and no indication of which element is at fault. These are the
# orders from ECMA-376 CT_Style and CT_PPrBase.
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


def ensure_child(parent, tag, order):
    """Find or create a child, inserting it at its schema-defined position."""
    found = parent.find(w(tag))
    if found is not None:
        return found
    el = etree.Element(w(tag))
    rank = order.index(tag) if tag in order else len(order)
    for existing in parent:
        name = etree.QName(existing).localname
        existing_rank = order.index(name) if name in order else len(order)
        if existing_rank > rank:
            existing.addprevious(el)
            return el
    parent.append(el)
    return el


def set_spacing(style, **kw):
    ppr = ensure_child(style, "pPr", STYLE_ORDER)
    sp = ensure_child(ppr, "spacing", PPR_ORDER)
    for key, val in kw.items():
        if val is not None:
            sp.set(w(key), str(val))


def set_flag(style, tag):
    """Add a boolean element such as <w:semiHidden/> in its correct position."""
    ensure_child(style, tag, STYLE_ORDER)


def set_ppr_flag(style, tag):
    ppr = ensure_child(style, "pPr", STYLE_ORDER)
    ensure_child(ppr, tag, PPR_ORDER)


def set_child_val(style, tag, value):
    ensure_child(style, tag, STYLE_ORDER).set(w("val"), value)


def transform_styles(root, mapping, config, report):
    styles = {s.get(w("styleId")): s for s in root.findall(w("style"))}
    dropped = set()

    # ---- drop ----
    for sid, why in mapping["drop"].items():
        if sid.startswith("_"):
            continue
        el = styles.get(sid)
        if el is None:
            report.append("  drop  %-34s (not present - already absent)" % sid)
            continue
        root.remove(el)
        del styles[sid]
        dropped.add(sid)
        report.append("  drop  %-34s %s" % (sid, why))

    # ---- rename (ids and display names) ----
    rename = {k: v for k, v in mapping["rename"].items() if not k.startswith("_")}
    idmap = {old: new["id"] for old, new in rename.items()}
    for old, new in rename.items():
        el = styles.get(old)
        if el is None:
            report.append("  WARN  rename source missing: %s" % old)
            continue
        el.set(w("styleId"), new["id"])
        set_child_val(el, "name", new["name"])
        styles[new["id"]] = styles.pop(old)
        report.append("  ren   %-34s -> %-28s %s" % (old, new["id"], new["name"]))

    # ---- rewrite every styleId reference, everywhere in this part ----
    rewrite_refs(root, idmap)

    # ---- add new styles ----
    for spec in mapping.get("add", []):
        el = etree.SubElement(root, w("style"))
        el.set(w("type"), "paragraph")
        el.set(w("customStyle"), "1")
        el.set(w("styleId"), spec["id"])
        set_child_val(el, "name", spec["name"])
        if spec.get("basedOn"):
            set_child_val(el, "basedOn", spec["basedOn"])
        if spec.get("next"):
            set_child_val(el, "next", spec["next"])
        if spec.get("spacing"):
            set_spacing(el, **spec["spacing"])
        if spec.get("keepNext"):
            set_ppr_flag(el, "keepNext")
        if "outlineLvl" in spec:
            ppr = ensure_child(el, "pPr", STYLE_ORDER)
            ensure_child(ppr, "outlineLvl", PPR_ORDER).set(
                w("val"), str(spec["outlineLvl"]))
        styles[spec["id"]] = el
        report.append("  add   %-34s %s" % (spec["id"], spec["name"]))

    # ---- retune ----
    for sid, ops in mapping["retune"].items():
        if sid.startswith("_"):
            continue
        el = styles.get(sid)
        if el is None:
            report.append("  WARN  retune target missing: %s" % sid)
            continue
        bits = []
        if "spacing" in ops:
            kw = {k: v for k, v in ops["spacing"].items() if not k.startswith("_")}
            set_spacing(el, **kw)
            bits.append("spacing(%s)" % ",".join("%s=%s" % i for i in kw.items()))
        if ops.get("keepNext"):
            set_ppr_flag(el, "keepNext")
            bits.append("keepNext")
        if ops.get("pageBreakBefore"):
            set_ppr_flag(el, "pageBreakBefore")
            bits.append("pageBreakBefore")
        if "outlineLvl" in ops:
            ppr = ensure_child(el, "pPr", STYLE_ORDER)
            ensure_child(ppr, "outlineLvl", PPR_ORDER).set(
                w("val"), str(ops["outlineLvl"]))
            bits.append("outlineLvl=%s" % ops["outlineLvl"])
        if ops.get("next"):
            set_child_val(el, "next", ops["next"])
            bits.append("next=%s" % ops["next"])
        if ops.get("semiHidden"):
            set_flag(el, "semiHidden")
            bits.append("semiHidden")
        if ops.get("unhideWhenUsed"):
            set_flag(el, "unhideWhenUsed")
            bits.append("unhideWhenUsed")
        if ops.get("match"):
            src = styles.get(ops["match"])
            if src is not None:
                copy_formatting(src, el)
                bits.append("formatting<-%s" % ops["match"])
        report.append("  tune  %-34s %s" % (sid, " ".join(bits)))

    # ---- global font and language ----
    font = mapping["global"]["font"]
    lang = mapping["global"]["lang"]
    retarget_rfonts(root, font)
    set_lang(root, lang)
    report.append("  glob  font -> %s, lang -> %s (symbol fonts preserved)" % (font, lang))
    return idmap, dropped


def add_caption_numbering(num_root, styles_root, mapping, report):
    """Attach style-linked automatic numbering to the caption styles.

    A <w:pStyle> back-link inside the numbering level is what makes Word number
    a paragraph the moment it is given that style - no Insert > Caption dialog,
    no per-document setup. The style also carries a matching <w:numPr> so the
    link holds from both directions.

    Trade-off, recorded deliberately: Word's own Insert > Caption uses SEQ
    fields instead, so a caption inserted that way starts its own count. Pick
    one convention per document. Style-linked was chosen because applying a
    style is the smoother action, which is what the review asked for.
    """
    spec = {k: v for k, v in mapping.get("add_numbering", {}).items()
            if not k.startswith("_")}
    first_num = num_root.find(w("num"))
    for sid, cfg in spec.items():
        # CT_Numbering is a sequence: every w:abstractNum must precede every
        # w:num. Appending both at the end interleaves them, and Word then
        # silently fails to resolve the numbering - the style applies but no
        # number appears.
        abstract = etree.Element(w("abstractNum"))
        if first_num is not None:
            first_num.addprevious(abstract)
        else:
            num_root.append(abstract)
        abstract.set(w("abstractNumId"), str(cfg["abstractNumId"]))
        mlt = etree.SubElement(abstract, w("multiLevelType"))
        mlt.set(w("val"), "singleLevel")
        lvl = etree.SubElement(abstract, w("lvl"))
        lvl.set(w("ilvl"), "0")
        for tag, val in (("start", "1"), ("numFmt", "decimal"),
                         ("pStyle", sid), ("lvlText", cfg["lvlText"]),
                         ("lvlJc", "left")):
            el = etree.SubElement(lvl, w(tag))
            el.set(w("val"), val)
        ppr = etree.SubElement(lvl, w("pPr"))
        ind = etree.SubElement(ppr, w("ind"))
        ind.set(w("left"), "0")
        ind.set(w("firstLine"), "0")

        num = etree.SubElement(num_root, w("num"))   # nums go at the end
        num.set(w("numId"), str(cfg["numId"]))
        ref = etree.SubElement(num, w("abstractNumId"))
        ref.set(w("val"), str(cfg["abstractNumId"]))

        # matching numPr on the style itself
        for st in styles_root.findall(w("style")):
            if st.get(w("styleId")) == sid:
                sppr = ensure_child(st, "pPr", STYLE_ORDER)
                numpr = ensure_child(sppr, "numPr", PPR_ORDER)
                for tag, val in (("ilvl", "0"), ("numId", str(cfg["numId"]))):
                    el = ensure_child(numpr, tag, ["ilvl", "numId"])
                    el.set(w("val"), val)
                break
        report.append("  num   %-24s auto-numbers as %r" % (sid, cfg["lvlText"]))


def renumber_appendices(num_root, styles_root, mapping, report):
    """Appendices as A1, A2; their subheadings as A1.1, A1.2.

    Edits the abstractNum that already backs the appendix style rather than
    adding a new one, so its indents and tab stops survive. The second level
    gets a pStyle back-link of its own, which is what makes applying the style
    number the paragraph.
    """
    cfg = mapping.get("appendix_numbering")
    if not cfg:
        return
    anchor = cfg["anchor_style"]
    target = None
    for a in num_root.findall(w("abstractNum")):
        for ps in a.iter(w("pStyle")):
            if ps.get(w("val")) == anchor:
                target = a
                break
        if target is not None:
            break
    if target is None:
        report.append("  WARN  appendix numbering: no abstractNum references %s" % anchor)
        return

    by_ilvl = {l.get(w("ilvl")): l for l in target.findall(w("lvl"))}
    numid = None
    for style in styles_root.findall(w("style")):
        if style.get(w("styleId")) == anchor:
            n = style.find(".//" + w("numId"))
            if n is not None:
                numid = n.get(w("val"))
            break

    for spec in cfg["levels"]:
        lvl = by_ilvl.get(str(spec["ilvl"]))
        if lvl is None:
            report.append("  WARN  appendix numbering: no ilvl %s" % spec["ilvl"])
            continue
        ensure_child(lvl, "lvlText", ["start", "numFmt", "pStyle", "lvlText",
                                      "lvlJc", "pPr", "rPr"]).set(
            w("val"), spec["lvlText"])
        ensure_child(lvl, "pStyle", ["start", "numFmt", "pStyle", "lvlText",
                                     "lvlJc", "pPr", "rPr"]).set(
            w("val"), spec["pStyle"])
        # numFmt matters as much as lvlText: the inherited level used
        # lowerLetter, so "A%1.%2" rendered as A1.a rather than A1.1.
        if spec.get("numFmt"):
            ensure_child(lvl, "numFmt", ["start", "numFmt", "pStyle", "lvlText",
                                         "lvlJc", "pPr", "rPr"]).set(
                w("val"), spec["numFmt"])
        if spec.get("start") is not None:
            ensure_child(lvl, "start", ["start", "numFmt", "pStyle", "lvlText",
                                        "lvlJc", "pPr", "rPr"]).set(
                w("val"), str(spec["start"]))
        report.append("  app   ilvl %s -> %-8s %s"
                      % (spec["ilvl"], spec["lvlText"], spec["pStyle"]))

        # the subheading style needs the matching numPr to complete the link
        if spec["ilvl"] > 0 and numid:
            for style in styles_root.findall(w("style")):
                if style.get(w("styleId")) == spec["pStyle"]:
                    sppr = ensure_child(style, "pPr", STYLE_ORDER)
                    numpr = ensure_child(sppr, "numPr", PPR_ORDER)
                    ensure_child(numpr, "ilvl", ["ilvl", "numId"]).set(
                        w("val"), str(spec["ilvl"]))
                    ensure_child(numpr, "numId", ["ilvl", "numId"]).set(
                        w("val"), numid)
                    break


def retext_numbering(root, mapping, report):
    """Rewrite lvlText values that carry German words.

    'Anhang %1' would prefix every appendix heading with the German for annex.
    Stripping it to a bare number makes the style language-neutral - the heading
    text itself already says what the section is.
    """
    rules = {k: v for k, v in mapping.get("numbering_text", {}).items()
             if not k.startswith("_")}
    n = 0
    for el in root.iter(w("lvlText")):
        val = el.get(w("val"))
        if val in rules:
            el.set(w("val"), rules[val])
            report.append("  lvl   lvlText %r -> %r" % (val, rules[val]))
            n += 1
    return n


def drop_style_refs(root, dropped):
    """Remove references to styles that no longer exist.

    numbering.xml holds w:pStyle back-links inside abstractNum/lvl - they are
    what make Word auto-number a paragraph the moment it gets a heading style.
    Dropping a style without clearing its back-link leaves numbering.xml
    pointing at nothing.
    """
    removed = 0
    for tag, _ in STYLE_REFS:
        for el in list(root.iter(tag)):
            if el.get(w("val")) in dropped:
                el.getparent().remove(el)
                removed += 1
    return removed


def retarget_rfonts(root, font):
    """Point body fonts at `font`, leaving symbol fonts alone.

    numbering.xml carries bullet glyphs in Symbol/Wingdings/Courier New; swapping
    those to Arial silently turns every bullet into a letter.
    """
    changed = 0
    for rfonts in root.iter(w("rFonts")):
        current = rfonts.get(w("ascii")) or rfonts.get(w("hAnsi"))
        if current in SYMBOL_FONTS:
            continue
        for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
            if rfonts.get(w(attr)) is not None and rfonts.get(w(attr)) not in SYMBOL_FONTS:
                rfonts.set(w(attr), font)
        for attr in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"):
            if rfonts.get(w(attr)) is not None:
                del rfonts.attrib[w(attr)]
        if current is not None:
            rfonts.set(w("ascii"), font)
            rfonts.set(w("hAnsi"), font)
            changed += 1
    return changed


def set_lang(root, lang):
    for el in root.iter(w("lang")):
        el.set(w("val"), lang)
        if el.get(w("eastAsia")) is not None:
            el.set(w("eastAsia"), lang)
    for el in root.iter(w("themeFontLang")):
        for attr in ("val", "eastAsia", "bidi"):
            if el.get(w(attr)) is not None:
                el.set(w(attr), lang)
    # activeWritingStyle is per-machine spell-check bookkeeping, not template
    # content. Drop it rather than translate it.
    for el in list(root.iter(w("activeWritingStyle"))):
        el.getparent().remove(el)


def copy_formatting(src, dest):
    """Replace dest's pPr/rPr with copies of src's - used for Caption, whose
    built-in NAME cannot change but whose formatting can."""
    import copy as _copy
    for tag in ("pPr", "rPr"):
        old = dest.find(w(tag))
        if old is not None:
            dest.remove(old)
        new = src.find(w(tag))
        if new is not None:
            placeholder = ensure_child(dest, tag, STYLE_ORDER)
            dest.replace(placeholder, _copy.deepcopy(new))


def rewrite_refs(root, idmap):
    """Rewrite every styleId reference in a part. This is the step that makes a
    rename a graph edit rather than a string replace."""
    n = 0
    for tag, attr in STYLE_REFS:
        for el in root.iter(tag):
            val = el.get(attr)
            if val in idmap:
                el.set(attr, idmap[val])
                n += 1
    return n


# --------------------------------------------------------------------------
# generated parts
# --------------------------------------------------------------------------

def gen_document(config):
    page = config["page"]
    tw = lambda cm: str(int(round(cm * CM)))
    return ("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="%s" xmlns:r="%s">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="11-Szoveg"/></w:pPr></w:p>
    <w:sectPr>
      <w:headerReference r:id="rId10" w:type="default"/>
      <w:footerReference r:id="rId11" w:type="default"/>
      <w:pgSz w:w="%d" w:h="%d"/>
      <w:pgMar w:top="%s" w:right="%s" w:bottom="%s" w:left="%s"
               w:header="708" w:footer="708" w:gutter="0"/>
      <w:cols w:space="708"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>
""" % (W, R, A4_W, A4_H,
       tw(page["margin_top_cm"]), tw(page["margin_right_cm"]),
       tw(page["margin_bottom_cm"]), tw(page["margin_left_cm"]))).encode("utf-8")


def gen_header(config):
    return ("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="%s" xmlns:r="%s">
  <w:p><w:pPr><w:pStyle w:val="Header"/></w:pPr></w:p>
</w:hdr>
""" % (W, R)).encode("utf-8")


def gen_footer(config):
    """Footer with real PAGE / SECTIONPAGES fields.

    SECTIONPAGES rather than NUMPAGES because the body section restarts its
    numbering at 1; NUMPAGES would count the cover and contents too. STYLEREF is
    deliberately avoided - it prints a Hungarian error string into the footer the
    moment a referenced style is missing.
    """
    return ("""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="%s" xmlns:r="%s">
  <w:p>
    <w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="right"/></w:pPr>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r><w:t>1</w:t></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
    <w:r><w:t xml:space="preserve"> / </w:t></w:r>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> SECTIONPAGES </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r><w:t>1</w:t></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
""" % (W, R)).encode("utf-8")


DOC_RELS = [
    ("rId1",  "styles",      "styles.xml"),
    ("rId2",  "numbering",   "numbering.xml"),
    ("rId3",  "settings",    "settings.xml"),
    ("rId4",  "webSettings", "webSettings.xml"),
    ("rId5",  "fontTable",   "fontTable.xml"),
    ("rId6",  "theme",       "theme/theme1.xml"),
    ("rId7",  "endnotes",    "endnotes.xml"),
    ("rId8",  "footnotes",   "footnotes.xml"),
    ("rId10", "header",      "header1.xml"),
    ("rId11", "footer",      "footer1.xml"),
]


def gen_document_rels():
    base = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    rels = "".join(
        '  <Relationship Id="%s" Type="%s%s" Target="%s"/>\n' % (rid, base, typ, target)
        for rid, typ, target in DOC_RELS)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="%s">\n%s</Relationships>\n' % (PR, rels)).encode("utf-8")


def gen_root_rels():
    base = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    pkg = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="%s">\n'
            '  <Relationship Id="rId1" Type="%sofficeDocument" Target="word/document.xml"/>\n'
            '  <Relationship Id="rId2" Type="%score-properties" Target="docProps/core.xml"/>\n'
            '  <Relationship Id="rId3" Type="%sextended-properties" Target="docProps/app.xml"/>\n'
            # Without this, Word ignores docProps/custom.xml completely: the
            # part sits in the package but every DOCPROPERTY field resolves to
            # nothing and CustomDocumentProperties reports zero.
            '  <Relationship Id="rId4" Type="%scustom-properties" Target="docProps/custom.xml"/>\n'
            '</Relationships>\n' % (PR, base, pkg, base, base)).encode("utf-8")


def gen_content_types(parts, as_template=False):
    main = ("application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"
            if as_template else
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml")
    o = "application/vnd.openxmlformats-officedocument.wordprocessingml."
    kinds = {
        "word/document.xml": main,
        "word/styles.xml": o + "styles+xml",
        "word/numbering.xml": o + "numbering+xml",
        "word/settings.xml": o + "settings+xml",
        "word/webSettings.xml": o + "webSettings+xml",
        "word/fontTable.xml": o + "fontTable+xml",
        "word/endnotes.xml": o + "endnotes+xml",
        "word/footnotes.xml": o + "footnotes+xml",
        "word/header1.xml": o + "header+xml",
        "word/footer1.xml": o + "footer+xml",
        "word/theme/theme1.xml": "application/vnd.openxmlformats-officedocument.theme+xml",
        "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        "docProps/custom.xml": "application/vnd.openxmlformats-officedocument.custom-properties+xml",
    }
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Types xmlns="%s">' % CT,
             '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
             '  <Default Extension="xml" ContentType="application/xml"/>',
             '  <Default Extension="png" ContentType="image/png"/>',
             '  <Default Extension="jpeg" ContentType="image/jpeg"/>']
    for part in parts:
        if part in kinds:
            lines.append('  <Override PartName="/%s" ContentType="%s"/>' % (part, kinds[part]))
    lines.append('</Types>')
    return ("\n".join(lines) + "\n").encode("utf-8")


def gen_core_props():
    dc = "http://purl.org/dc/elements/1.1/"
    cp = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="%s" xmlns:dc="%s">\n'
            '  <dc:title></dc:title>\n'
            '  <dc:creator>Medek Mernoki Iroda kft</dc:creator>\n'
            '  <dc:language>hu-HU</dc:language>\n'
            '</cp:coreProperties>\n' % (cp, dc)).encode("utf-8")


def gen_empty_custom_props():
    """Placeholder so the package relationship has a target. build replaces this
    with the real document properties."""
    ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Properties xmlns="%s" xmlns:vt="%s"></Properties>\n'
            % (ns, vt)).encode("utf-8")


def gen_app_props():
    ep = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Properties xmlns="%s">\n'
            '  <Application>Microsoft Office Word</Application>\n'
            '  <Company>Medek Mernoki Iroda kft</Company>\n'
            '</Properties>\n' % ep).encode("utf-8")


# --------------------------------------------------------------------------

def pretty(data, config):
    """Delegate to medtpl's pretty-printer.

    Deliberately not a second implementation: if derive and medtpl indented
    differently, `medtpl roundtrip` would fail on a master that is actually fine,
    and the assertion that makes the exploded tree trustworthy would be useless.
    One printer, one output.
    """
    sys.path.insert(0, str(TEMPLATES))
    from medtpl import pretty_xml, has_text_content
    if has_text_content(data):
        raise SystemExit("refusing to pretty-print a part with text content")
    return pretty_xml(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite an existing master/")
    args = ap.parse_args()

    mapping = load(MAP_FILE)
    config = load(CONFIG_FILE)

    if MASTER.exists() and any(MASTER.iterdir()) and not args.force and not args.dry_run:
        sys.exit("error: %s already exists and is not empty.\n"
                 "  derive is a ONE-SHOT step - master/ is the source of truth once written.\n"
                 "  Use --force only if you really mean to discard it." % MASTER)

    src = Path(mapping["source"])
    if not src.is_file():
        sys.exit("error: WG master not found at %s" % src)

    zf = zipfile.ZipFile(src)
    have = set(zf.namelist())
    report = []
    out = {}

    # ---- carried, transformed parts ----
    idmap = {}
    styles_root = parse(zf.read("word/styles.xml"))
    report.append("styles.xml:")
    idmap, dropped = transform_styles(styles_root, mapping, config, report)
    out["word/styles.xml"] = serialise(styles_root)

    font = mapping["global"]["font"]
    lang = mapping["global"]["lang"]
    for part in CARRY:
        if part == "word/styles.xml" or part not in have:
            continue
        root = parse(zf.read(part))
        refs = rewrite_refs(root, idmap)
        gone = drop_style_refs(root, dropped)
        if part == "word/numbering.xml":
            retext_numbering(root, mapping, report)
            add_caption_numbering(root, styles_root, mapping, report)
            renumber_appendices(root, styles_root, mapping, report)
            out["word/styles.xml"] = serialise(styles_root)  # numPr was added
        fonts = retarget_rfonts(root, font)
        set_lang(root, lang)
        if part in ("word/fontTable.xml", "word/theme/theme1.xml"):
            retarget_fonts(root, font)
        out[part] = serialise(root)
        notes = []
        if refs:
            notes.append("%d style refs" % refs)
        if fonts:
            notes.append("%d font refs" % fonts)
        if gone:
            notes.append("cleared %d refs to dropped styles" % gone)
        if notes:
            report.append("%s: rewrote %s" % (part, ", ".join(notes)))

    # ---- generated parts ----
    out["word/document.xml"] = gen_document(config)
    out["word/header1.xml"] = gen_header(config)
    out["word/footer1.xml"] = gen_footer(config)
    out["word/_rels/document.xml.rels"] = gen_document_rels()
    out["_rels/.rels"] = gen_root_rels()
    out["docProps/core.xml"] = gen_core_props()
    out["docProps/app.xml"] = gen_app_props()
    out["docProps/custom.xml"] = gen_empty_custom_props()
    # sorted(set(...)): a duplicate PartName override is invalid OOXML and Word
    # rejects the package outright.
    out["[Content_Types].xml"] = gen_content_types(sorted(set(out.keys())))
    report.append("generated: document.xml, header1.xml, footer1.xml, rels, content-types, docProps")
    report.append("  (not inherited from WG - their document and headers embed the WG wordmark)")

    # ---- forbidden-content sweep ----
    problems = []
    for part, data in out.items():
        text = data.decode("utf-8", "replace")
        for bad in config["strip"]["forbidden_substrings"]:
            if bad in text:
                problems.append("%s contains %r" % (part, bad))

    print("\n".join(report))
    print()
    if problems:
        print("FORBIDDEN CONTENT STILL PRESENT:")
        for p in problems:
            print("  ! " + p)
    else:
        print("forbidden-content sweep: clean (no Frutiger, de-CH/de-DE, WG marks)")

    dropped = sorted(have - set(out.keys()))
    print("\ndropped %d source parts, including the WG wordmark and customXml bindings" % len(dropped))

    if args.dry_run:
        print("\n[dry run] would write %d parts to %s" % (len(out), MASTER))
        return 0

    # ---- write the exploded tree ----
    # Clear the contents rather than the directory itself: OneDrive keeps a
    # handle on synced folders and rmtree of the root fails with WinError 5.
    if MASTER.exists():
        for child in sorted(MASTER.rglob("*"), key=lambda p: -len(p.parts)):
            try:
                child.unlink() if child.is_file() else child.rmdir()
            except OSError:
                pass
    MASTER.mkdir(parents=True, exist_ok=True)
    manifest = {"_note": "Written by derive.py. Hashes let medtpl check detect hand edits.",
                "source": str(src), "parts": {}}
    pretty_set = set(config["xml_format"]["pretty_print"])
    for part in sorted(out):
        data = out[part]
        if part in pretty_set:
            data = pretty(data, config)
        dest = MASTER / part
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        manifest["parts"][part] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "format": "pretty" if part in pretty_set else "verbatim",
        }
    (MASTER / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\nwrote %d parts to %s" % (len(out), MASTER))
    print("next: review `git diff` of master/word/styles.xml - that review is the")
    print("      whole reason this architecture was chosen.")
    return 0


def retarget_fonts(root, font):
    for el in root.iter():
        tag = etree.QName(el).localname
        if tag in ("latin", "ea", "cs") and el.get("typeface"):
            el.set("typeface", font)
        if tag == "font" and el.get(w("name")):
            el.set(w("name"), font)


if __name__ == "__main__":
    sys.exit(main())
