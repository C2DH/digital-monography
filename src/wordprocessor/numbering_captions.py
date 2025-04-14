import docx.document
import docx.shared
import docx.styles.style
import docx.text.paragraph
import docx.text.run
import docx.oxml.shared
import docx.oxml.text.font
import docx.oxml.text.parfmt
import docx.oxml.text.paragraph
import docx.oxml.text.run
import docx.oxml.xmlchemy

try:
    from constants import CAPTION_ALLOWED_ITEMS
    from metadata import DocumentMetadata
except (ImportError, ModuleNotFoundError):
    from .constants import CAPTION_ALLOWED_ITEMS  # type: ignore
    from .metadata import DocumentMetadata  # type: ignore


def add_chapter_number_to_captions(
    doc: docx.document.Document, metadata: DocumentMetadata
) -> None:
    """
    Find caption paragraphs and add chapter number to the automatic numbering.
    E.g., a caption beginning with "Figure 1: ..." will be changed to "Figure X.1: ...",
    where X is the chapter number.

    Note that all the cross-references should reflect this change upon fields update.
    Read more about fields in EMCA-376 part 1, §17.16.

    This solution assumes that captions have the following structure:
    ```xml
    <p>
        <pPr>
            <pStyle w:val="Caption" />
        </pPr>
        <bookmarkStart w:name="_Ref{REF_NUMBER}" />
        <r>
            <rPr>
                <b />
                <bCs />
            </rPr>
            <t xml:space="preserve">
                Figure
            </t>
        </r>
        <r>
            <rPr>
                <b />
                <bCs />
            </rPr>
            <fldChar w:fldCharType="begin" />
        </r>
    ```
    Note that only complex fields are supported (fildChar) and not fldSimple.
    Once a begin of fieldChar has been found in a caption-styled paragraph,
    the number of a chapter is concatenated to the text of a previous run,
    which should be the caption type (e.g. "Figure" or "Table").
    """

    captions_pstyle_elems: list[docx.oxml.shared.CT_String] = doc.element.xpath(
        "//w:p/w:pPr/w:pStyle[@w:val='Caption']"
    )
    for caption_pstyle_el in captions_pstyle_elems:
        pPr: docx.oxml.text.parfmt.CT_PPr = caption_pstyle_el.getparent()
        p: docx.oxml.text.paragraph.CT_P = pPr.getparent()
        assert isinstance(p, docx.oxml.text.paragraph.CT_P)
        complex_fields = p.xpath("./w:r[child::w:fldChar[@w:fldCharType='begin']]")
        for field in complex_fields:
            assert isinstance(field, docx.oxml.text.run.CT_R)
            prev: docx.oxml.text.run.CT_R = field.getprevious()
            if _is_caption_item(prev):
                assert isinstance(prev, docx.oxml.text.run.CT_R)
                prev.text = f"{prev.text}{metadata.get_chapter_number()}."


def _is_caption_item(node: str) -> bool:
    if not isinstance(node, docx.oxml.text.run.CT_R):
        return False
    for caption_item in CAPTION_ALLOWED_ITEMS:
        if caption_item in node.text.lower():
            return True
    return False
