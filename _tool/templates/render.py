"""Document rendering for medtpl: layout JSON -> WordprocessingML.

Stdlib only. Generates document.xml, plus headers that embed the practice logo.

Everything here writes XML as text rather than building a tree. That is not
laziness: document.xml carries w:t, so the rest of the toolchain stores it
byte-verbatim and never pretty-prints it. Generating it as text keeps what is
written and what is stored identical.
"""

from xml.sax.saxutils import escape

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
)

CM_TWIP = 567.0
CM_EMU = 360000.0
DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def esc(text):
    return escape(str(text))


def run(text, bold=False, italic=False, caps=False, size=None, colour=None):
    props = ""
    if bold:
        props += "<w:b/>"
    if italic:
        props += "<w:i/>"
    if caps:
        props += "<w:caps/>"
    if size:
        props += '<w:sz w:val="%d"/>' % int(size * 2)  # half-points
    if colour:
        props += '<w:color w:val="%s"/>' % colour
    rpr = "<w:rPr>%s</w:rPr>" % props if props else ""
    # xml:space preserve keeps leading and trailing spaces, which Word eats otherwise
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(text))


def field(instr, placeholder=""):
    """A real Word field. The placeholder is what shows until F9 updates it."""
    return (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve">%s</w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r><w:t>%s</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>' % (esc(instr), esc(placeholder))
    )


def docprop(name, ctx=None):
    """A DOCPROPERTY field, with its cached result set to the actual value.

    A Word field has two halves: the instruction, and a cached result that is
    what you SEE until the field is updated. Setting a value therefore means
    setting the document property and the cached result - never replacing the
    field with literal text. Do that and the value stops being linked: editing
    the property no longer changes the document, and the single-source-of-truth
    the field existed for is gone.

    Falls back to the property name only when no value is known, so an unfilled
    field is visibly unfilled rather than silently blank.
    """
    value = name
    if ctx is not None:
        value = (ctx.get("docprops") or {}).get(name) or name
    return field(' DOCPROPERTY "%s" \* MERGEFORMAT ' % name, value)


def para(style=None, content="", extra=""):
    ppr = ""
    if style:
        ppr += '<w:pStyle w:val="%s"/>' % esc(style)
    ppr += extra
    ppr = "<w:pPr>%s</w:pPr>" % ppr if ppr else ""
    return "<w:p>%s%s</w:p>" % (ppr, content)


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(spec):
    style = spec.get("style", "TableGrid")
    widths = spec.get("widths")
    rows = spec.get("rows", [])
    header = spec.get("header")
    cell_style = spec.get("cell_style", "18-Tablazatszoveg")
    head_style = spec.get("head_style", "16-Tablazatcim")

    total = spec.get("total_width_twips", 9071)  # 16.0 cm usable width
    ncols = len(header or (rows[0] if rows else [""]))
    if not widths:
        widths = [total // ncols] * ncols

    # Borders off at table level; the only rule is drawn under the header row,
    # as a bottom border on those cells. Quieter than a full grid and it lets
    # the numbers carry the structure rather than the lines.
    out = ['<w:tbl><w:tblPr><w:tblStyle w:val="%s"/>' % esc(style),
           '<w:tblW w:w="%d" w:type="dxa"/>' % total,
           '<w:tblBorders>'
           '<w:top w:val="none" w:sz="0" w:color="auto"/>'
           '<w:left w:val="none" w:sz="0" w:color="auto"/>'
           '<w:bottom w:val="none" w:sz="0" w:color="auto"/>'
           '<w:right w:val="none" w:sz="0" w:color="auto"/>'
           '<w:insideH w:val="none" w:sz="0" w:color="auto"/>'
           '<w:insideV w:val="none" w:sz="0" w:color="auto"/>'
           '</w:tblBorders></w:tblPr>',
           '<w:tblGrid>%s</w:tblGrid>'
           % "".join('<w:gridCol w:w="%d"/>' % x for x in widths)]

    # White: the rule under the header carries the separation on its own, and a
    # grey band prints as a muddy grey on office printers.
    HEADER_SHADE = spec.get("header_shade", "FFFFFF")

    def emit_row(cells, style_name, bold, is_header):
        trpr = "<w:trPr><w:tblHeader/></w:trPr>" if is_header else ""
        extra_tc = ""
        if is_header:
            extra_tc = ('<w:tcBorders><w:bottom w:val="single" w:sz="8" '
                        'w:color="808080"/></w:tcBorders>'
                        '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>'
                        % HEADER_SHADE)
        tds = []
        for i, cell in enumerate(cells):
            tds.append(
                '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>%s</w:tc>'
                % (widths[i] if i < len(widths) else widths[-1], extra_tc,
                   para(style_name, run(cell, bold=bold))))
        out.append("<w:tr>%s%s</w:tr>" % (trpr, "".join(tds)))

    if header:
        emit_row(header, head_style, True, True)
    for row in rows:
        emit_row(row, cell_style, False, False)
    out.append("</w:tbl>")
    # A table may not be the last block in a section - Word requires a following
    # paragraph or the document is malformed.
    out.append(para("11-Szoveg"))
    return "".join(out)


def picture(rel_id, width_cm, height_cm, name="Kep", doc_pr_id=1, svg_rel=None):
    """An inline picture. If svg_rel is given, Word renders the SVG as vector.

    Word 2016+ supports SVG through an extension on a:blip. The raster in
    r:embed is NOT redundant - it is the mandatory fallback for older Word,
    for LibreOffice, and for anything that reads the package without
    understanding the extension. Both parts have to be in the package.
    """
    cx, cy = int(width_cm * CM_EMU), int(height_cm * CM_EMU)
    if svg_rel:
        blip = ('<a:blip r:embed="%s"><a:extLst>'
                '<a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
                '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
                'r:embed="%s"/>'
                '</a:ext></a:extLst></a:blip>' % (esc(rel_id), esc(svg_rel)))
    else:
        blip = '<a:blip r:embed="%s"/>' % esc(rel_id)
    return (
        '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="%d" cy="%d"/>'
        '<wp:docPr id="%d" name="%s"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic>'
        '<pic:nvPicPr><pic:cNvPr id="0" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill>%s<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r>'
        % (cx, cy, doc_pr_id, esc(name), esc(name), blip, cx, cy)
    )


def sect_pr(page, header_rel=None, footer_rel=None, title_page=False,
            restart_at=None, sect_type=None):
    tw = lambda cm: int(round(cm * CM_TWIP))
    bits = []
    if sect_type:
        bits.append('<w:type w:val="%s"/>' % sect_type)
    if header_rel:
        bits.append('<w:headerReference r:id="%s" w:type="default"/>' % header_rel)
    if footer_rel:
        bits.append('<w:footerReference r:id="%s" w:type="default"/>' % footer_rel)
    bits.append('<w:pgSz w:w="11906" w:h="16838"/>')
    bits.append('<w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" '
                'w:header="708" w:footer="708" w:gutter="0"/>'
                % (tw(page["margin_top_cm"]), tw(page["margin_right_cm"]),
                   tw(page["margin_bottom_cm"]), tw(page["margin_left_cm"])))
    if restart_at is not None:
        bits.append('<w:pgNumType w:start="%d"/>' % restart_at)
    if title_page:
        bits.append("<w:titlePg/>")
    bits.append('<w:cols w:space="708"/><w:docGrid w:linePitch="360"/>')
    return "<w:sectPr>%s</w:sectPr>" % "".join(bits)


class Ctx(dict):
    """Carries token values and hands out unique drawing ids."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._id = 100

    def next_id(self):
        self._id += 1
        return self._id


TOKEN_RE = None


def substitute(text, ctx):
    """Fill {{TOKEN}} values; anything left over becomes a visible placeholder.

    A template built with no project attached would otherwise ship literal
    {{ADDRESS}} text. Turning the leftovers into <cim> makes it obvious they are
    blanks to fill, and keeps them findable with Word's search.
    """
    global TOKEN_RE
    if TOKEN_RE is None:
        import re as _re
        TOKEN_RE = _re.compile(r"\{\{([A-Z_]+)\}\}")
    for key, val in ctx.get("tokens", {}).items():
        text = text.replace("{{%s}}" % key, str(val))
    return TOKEN_RE.sub(lambda m: "<%s>" % m.group(1).lower(), text)


def render_block(block, ctx):
    """One content block from a layout JSON -> XML."""
    if "pagebreak" in block:
        return page_break()
    if "table" in block:
        return table(block["table"])
    if "signature" in block:
        # A signature image is personal, so it is never bundled with the shared
        # template - it is pulled from assets/ only when one is present for the
        # named designer, and falls back to a ruled line otherwise.
        rel = ctx.get("signature_rel")
        if rel:
            return para(block.get("style", "48-Alairas"),
                        picture(rel, ctx.get("signature_w_cm", 4.0),
                                ctx.get("signature_h_cm", 1.6),
                                "Alairas", ctx.next_id()))
        return para(block.get("style", "48-Alairas"),
                    run("………………………………………"))
    if "image" in block:
        return para(block.get("style", "15-Abra"),
                    picture(ctx["logo_rel"], block.get("width_cm", 8),
                            block.get("height_cm", 8), block.get("name", "Kep"),
                            ctx.next_id()))
    if "docprop" in block:
        label = block.get("label", "")
        inline = block.get("inline", False)
        content = (run(label + (" " if inline else "")) if label else "")             + docprop(block["docprop"], ctx)
        extra = ("" if inline or not label
                 else '<w:tabs><w:tab w:val="left" w:pos="3402"/></w:tabs>')
        return para(block.get("style"), content, extra)
    if "field" in block:
        return para(block.get("style"), field(block["field"], block.get("placeholder", "")))
    if "empty" in block:
        return "".join(para(block.get("style", "11-Szoveg")) for _ in range(block["empty"]))

    text = substitute(block.get("text", ""), ctx)
    content = run(text, bold=block.get("bold", False), italic=block.get("italic", False),
                  caps=block.get("caps", False), size=block.get("size"),
                  colour=block.get("colour")) if text or not block.get("style") else ""
    extra = ""
    if block.get("align"):
        extra += '<w:jc w:val="%s"/>' % block["align"]
    if block.get("numbered"):
        extra += '<w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%d"/></w:numPr>' % (
            block.get("ilvl", 0), block["numbered"])
    return para(block.get("style"), content, extra)


def render_document(layout, config, ctx):
    page = config["page"]
    body = []
    sections = layout["sections"]
    last = len(sections) - 1
    for i, section in enumerate(sections):
        for block in section.get("content", []):
            body.append(render_block(block, ctx))
        sp = sect_pr(
            page,
            header_rel=ctx.get("header_rel"),
            footer_rel=ctx.get("footer_rel"),
            title_page=section.get("title_page", False),
            restart_at=section.get("restart_page_numbering"),
            sect_type=None if i == last else section.get("break", "nextPage"),
        )
        if i == last:
            body.append(sp)
        else:
            # A non-final section's sectPr lives inside a paragraph's pPr.
            body.append("<w:p><w:pPr>%s</w:pPr></w:p>" % sp)
    return (DECL + "<w:document %s><w:body>%s</w:body></w:document>\n"
            % (NS, "".join(body))).encode("utf-8")


def render_header(ctx, with_logo=True, right_text="", lines=None):
    """Practice identification left, logo right.

    Built as a borderless two-cell table rather than tab stops. Tabs work for a
    single line, but the left block here is several lines (practice, address,
    document name) while the logo must stay on the first - a table is the only
    structure that keeps those independent. Borders are explicitly set to none:
    inheriting Table Grid would draw a box round the header.
    """
    rel = ctx.get("logo_rel_header") or ctx.get("logo_rel")
    left_w, right_w = 7200, 1871          # of the 9071 twip text width

    left = ""
    for spec in (lines or []):
        left += para(spec.get("style", "12-Infoszoveg"),
                     run(substitute(spec.get("text", ""), ctx),
                         bold=spec.get("bold", False),
                         size=spec.get("size")))
    if right_text:
        left += para("12-Infoszoveg", run(substitute(right_text, ctx)))
    if not left:
        left = para("Header")

    right = para("Header")
    if with_logo and rel:
        h = ctx.get("logo_h_cm", 1.1)
        right = para("Header",
                     picture(rel, ctx.get("logo_w_cm", h), h, "Medek logo",
                             ctx.next_id(),
                             svg_rel=ctx.get("logo_svg_rel_header")),
                     '<w:jc w:val="right"/>')

    cell = ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>'
            '<w:vAlign w:val="%s"/></w:tcPr>%s</w:tc>')
    tbl = (
        '<w:tbl><w:tblPr>'
        '<w:tblW w:w="9071" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="none" w:sz="0" w:color="auto"/>'
        '<w:left w:val="none" w:sz="0" w:color="auto"/>'
        '<w:bottom w:val="none" w:sz="0" w:color="auto"/>'
        '<w:right w:val="none" w:sz="0" w:color="auto"/>'
        '<w:insideH w:val="none" w:sz="0" w:color="auto"/>'
        '<w:insideV w:val="none" w:sz="0" w:color="auto"/>'
        '</w:tblBorders>'
        '<w:tblCellMar>'
        '<w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/>'
        '</w:tblCellMar>'
        '</w:tblPr>'
        '<w:tblGrid><w:gridCol w:w="%d"/><w:gridCol w:w="%d"/></w:tblGrid>'
        '<w:tr>%s%s</w:tr>'
        '</w:tbl>' % (left_w, right_w,
                      cell % (left_w, "center", left),
                      cell % (right_w, "center", right))
    )
    # A table may not be the last element in a header part.
    return (DECL + "<w:hdr %s>%s%s</w:hdr>\n"
            % (NS, tbl, para("Header"))).encode("utf-8")


def render_footer_lines(ctx, lines, page_numbers=True):
    """Footer built from a list of blocks, so it can carry DOCPROPERTY fields.

    The review asked for the original document's footer convention - project
    description and site address on every page. Those same values appear on the
    cover and in the nyilatkozat, which is exactly the case for fields: one
    edit updates all of them.
    """
    out = []
    for spec in lines:
        content = ""
        for piece in spec.get("parts", []):
            if "docprop" in piece:
                content += docprop(piece["docprop"], ctx)
            else:
                content += run(substitute(piece.get("text", ""), ctx))
        out.append(para(spec.get("style", "Footer"), content,
                        '<w:jc w:val="%s"/>' % spec.get("align", "center")))
    if page_numbers:
        content = field(" PAGE ", "1") + run(" / ") + field(" SECTIONPAGES ", "1")
        out.append(para("Footer", content, '<w:jc w:val="right"/>'))
    return (DECL + "<w:ftr %s>%s</w:ftr>\n" % (NS, "".join(out))).encode("utf-8")


def render_footer(ctx, left_text=""):
    """PAGE / SECTIONPAGES, deliberately not NUMPAGES.

    The body section restarts numbering at 1, so NUMPAGES would also count the
    cover and contents and every footer would read "3 / 19". STYLEREF is avoided
    entirely: when a referenced style is missing it prints a Hungarian error
    string into the footer of every page.
    """
    content = ""
    if left_text:
        content += run(substitute(left_text, ctx) + "\t")
    content += field(" PAGE ", "1") + run(" / ") + field(" SECTIONPAGES ", "1")
    return (DECL + "<w:ftr %s>%s</w:ftr>\n"
            % (NS, para("Footer", content, '<w:jc w:val="right"/>'))).encode("utf-8")
