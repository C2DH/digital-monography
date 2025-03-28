import docx.document
import docx.shared
import docx.styles.style
import docx.text.paragraph
import docx.text.run
import docx.oxml.text.font
import docx.oxml.text.paragraph
import docx.oxml.xmlchemy

try:
    from constants import COLOR_DIGITAL_ONLY, COLOR_PAPER_ONLY
except (ImportError, ModuleNotFoundError):
    from .constants import COLOR_DIGITAL_ONLY, COLOR_PAPER_ONLY  # type: ignore


def remove_parts_and_highlights_due_to_conditional_rendering(
    doc: docx.document.Document,
) -> None:
    """
    Iterate docx document over paragraphs and tables to:
    * remove paragraphs marked as digital_only if the whole paragraph was marked,
    * clear runs marked as digital_only,
    * remove highlights from paragraphs and runs marked as paper_only
      leaving those parts.
    The document is modified in place.
    """
    for p in doc.paragraphs:
        if _is_whole_paragraph_only_for_digital(p):
            _remove_whole_paragraph(p)
            continue

        for hyperlink in p.hyperlinks:
            _handle_highlights_in_runs(hyperlink.runs)
        for r in p.runs:
            if (r.element.rPr is None) or (r.element.rPr.highlight is None):
                continue
            if COLOR_DIGITAL_ONLY in r.element.rPr.highlight.values():
                r.clear()
            elif COLOR_PAPER_ONLY in r.element.rPr.highlight.values():
                r.element.rPr._remove_highlight()

    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _handle_highlights_in_runs(p.runs, tbl._element)
                    for link in p.hyperlinks:
                        _handle_highlights_in_runs(link.runs, tbl._element)


##### useful snippets #####
# # changing styles
# style = doc.styles["Normal"]
# style: docx.styles.style._ParagraphStyle
# style.font.color.rgb = docx.shared.RGBColor(235, 64, 52)
# # or
# # style.font.color.rgb = (docx.shared.RGBColor)(style.font.color.rgb).from_string("eb4034")
# style.font.size = docx.shared.Pt(12)
# style.font.bold = True
# style.font.italic = True
# style.font.underline = True
# # accessing xml
# print(doc._element.xml)
############################


def _is_whole_paragraph_only_for_digital(p: docx.text.paragraph.Paragraph) -> bool:
    """
    If paragraph's properties (pPr) have a highlight,
    then whole paragraph is highlighted.
    If so, check if the whole paragraph is marked as digital_only.

    Example of a paragraph where the function should return True:
    ```xml
    <p>
        <pPr>
            <pStyle w:val="BodyText" />
            <rPr>
                <highlight w:val="lightGray" />
            </rPr>
        </pPr>
        ...
    ```
    Example of a paragraph where the function should return False:
    ```xml
    <p>
        <pPr>
            <pStyle w:val="BodyText" />
        </pPr>
        ...
    ```
    """
    # check highlights in paragraph properties
    highlights = set()
    _highlights: list[docx.oxml.text.font.CT_Highlight] = []
    _highlights = p._element.xpath(".//w:pPr/w:rPr/w:highlight")
    for h in _highlights:
        highlights.update(h.values())
    if len(highlights) == 1 and COLOR_DIGITAL_ONLY in highlights:
        return True
    # check highlights in properties of all runs in the paragraph
    highlights = set()
    for run in p.runs:
        if run.element.rPr is not None and run.element.rPr.highlight is not None:
            highlights.update(run.element.rPr.highlight.values())
    if len(highlights) == 1 and COLOR_DIGITAL_ONLY in highlights:
        return True
    # else
    return False


def _remove_whole_paragraph(p: docx.text.paragraph.Paragraph) -> None:
    par: docx.oxml.text.paragraph.CT_P = p._element
    assert isinstance(par, docx.oxml.text.paragraph.CT_P)
    par_parent: docx.oxml.document.CT_Body = par.getparent()
    assert isinstance(par_parent, docx.oxml.document.CT_Body)
    par_parent.remove(par)
    par._p = None
    par._element = None


def _handle_highlights_in_runs(
    runs: list[docx.text.run.Run],
    el_to_clear: docx.oxml.xmlchemy.BaseOxmlElement | None = None,
) -> None:
    for r in runs:
        if (r.element.rPr is None) or (r.element.rPr.highlight is None):
            pass
        elif COLOR_DIGITAL_ONLY in r.element.rPr.highlight.values():
            if el_to_clear is not None:
                assert isinstance(el_to_clear, docx.oxml.xmlchemy.BaseOxmlElement)
                el_to_clear.clear()
            else:
                r.clear()
        elif COLOR_PAPER_ONLY in r.element.rPr.highlight.values():
            r.element.rPr._remove_highlight()
