import argparse
import datetime
import logging
import pathlib
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
import json

try:
    from constants import CAPTION_ALLOWED_ITEMS, IS_DEBUG
    from conditional_rendering import (
        remove_parts_and_highlights_due_to_conditional_rendering,
    )
    from metadata import DocumentMetadata
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .constants import CAPTION_ALLOWED_ITEMS, IS_DEBUG  # type: ignore
    from .conditional_rendering import remove_parts_and_highlights_due_to_conditional_rendering  # type: ignore
    from .metadata import DocumentMetadata  # type: ignore
    from .keys import KeyPath  # type: ignore


parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path", type=str)


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_preparer.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler() -> tuple[docx.document.Document, dict[str, DocumentMetadata]]:
    key: KeyPath = KeyPath("/tmp/efs/docx2docx/")
    # book_metadata: dict[str, DocumentMetadata] = {}
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
    # for meta_file in (key / "_metadata").glob("**/*.json"):
    #     meta_file: KeyPath
    #     with meta_file.open("r") as f:
    #         metadata = DocumentMetadata(meta_file)
    #         metadata.from_json(json.load(f))
    #         book_metadata[meta_file.stem] = metadata

    book_metadata = _read_book_metadata(key)
    # per each doc
    metadata = book_metadata["02_assets_and_links"]
    doc = docx.Document("/tmp/efs/docx2docx/02_assets_and_links.docx")
    # doc = docx.Document("/tmp/efs/docx2docx/ref-n-target.docx")
    remove_parts_and_highlights_due_to_conditional_rendering(doc)
    # prepare_ref_targets_in_headers(doc, book_metadata)
    prepare_ref_targets_in_captions(doc, metadata)
    # prepare_ref_targets_in_footnotes(doc, book_metadata)
    # prepare_references(doc, book_metadata)
    # refs = doc.element.xpath("//w:instrText[contains(text(), 'REF ')]")
    # substitute(doc, book_metadata)

    # add_chapter_number(doc, book_metadata)
    # _merge_docs(key, book_metadata)
    return doc, book_metadata


def prepare_ref_targets_in_captions(
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


def prepare_references(
    doc: docx.document.Document, book_metadata: dict[str, DocumentMetadata]
):
    return
    for child in doc.paragraphs[0].runs[13].element.getchildren():
        if isinstance(child, docx.oxml.text.run.CT_Text):
            print("child.text", child.text)
            child.text = "666"
            print("child.text", child.text)
    return

    ##### refs

    doc.paragraphs[0].hyperlinks[0].fragment == "_Heading"
    doc.paragraphs[0].hyperlinks[0].text == "Link to direct heading"
    doc.paragraphs[0].hyperlinks[0].address == ""
    doc.paragraphs[0].hyperlinks[0].url == ""

    # check if you can replace _r with element, should be the same obj
    doc.paragraphs[0].runs[3]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[3]._r.values() == ["002D78BD"]
    doc.paragraphs[0].runs[3]._r.getchildren()[0].values() == ["begin"]
    doc.paragraphs[0].runs[3]._r.getchildren()[0].tag.endswith("fldChar")
    doc.paragraphs[0].runs[3]._r.getchildren()[0].text == ""

    doc.paragraphs[0].runs[4]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[4]._r.values() == ["002D78BD"]
    doc.paragraphs[0].runs[4]._r.getchildren()[0].text == r" REF _Ref193896300 \h "
    doc.paragraphs[0].runs[4]._r.getchildren()[0].values() == ["preserve"]
    doc.paragraphs[0].runs[4]._r.getchildren()[0].tag.endswith("instrText")
    doc.paragraphs[0].runs[4]._r.getchildren()[0].text == ""

    doc.paragraphs[0].runs[5]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[5]._r.values() == ["002D78BD"]
    doc.paragraphs[0].runs[5]._r.getchildren()[0].values() == ["separate"]
    doc.paragraphs[0].runs[5]._r.getchildren()[0].tag.endswith("fldChar")
    doc.paragraphs[0].runs[5]._r.getchildren()[0].text == ""

    doc.paragraphs[0].runs[6]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[6]._r.values() == ["002D78BD"]
    doc.paragraphs[0].runs[6]._r.getchildren()[0].text == "Heading"

    doc.paragraphs[0].runs[7]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[7]._r.values() == ["002D78BD"]
    doc.paragraphs[0].runs[7]._r.getchildren()[0].values() == ["end"]
    doc.paragraphs[0].runs[7]._r.getchildren()[0].tag.endswith("fldChar")
    doc.paragraphs[0].runs[7]._r.getchildren()[0].text == ""

    doc.paragraphs[0].runs[9]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[9]._r.values() == ["00602226"]
    doc.paragraphs[0].runs[9]._r.getchildren()[0].values() == ["begin"]
    doc.paragraphs[0].runs[9]._r.getchildren()[0].tag.endswith("fldChar")
    doc.paragraphs[0].runs[9]._r.getchildren()[0].text == ""

    doc.paragraphs[0].runs[10]._r.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[10]._r.values() == ["00602226"]
    doc.paragraphs[0].runs[10]._r.getchildren()[0].values() == ["preserve"]
    doc.paragraphs[0].runs[10]._r.getchildren()[0].tag.endswith("fldChar")
    doc.paragraphs[0].runs[10]._r.getchildren()[0].text == r" REF _Ref193903648 \h "

    doc.paragraphs[0].runs[10].element.keys()[0].endswith("rsidR")
    doc.paragraphs[0].runs[10].element.values() == ["00602226"]
    for child in doc.paragraphs[0].runs[13].element.getchildren():
        if isinstance(child, docx.oxml.text.run.CT_Text):
            child.text == "1"  # <== replace txt in ref !!
        # ref.target_id = "f-ref-n-target-ref193903648"
        # target.pk = "f-ref-n-target-ref193903648"
        # target.html = '<data value=" SEQ Table \* ARABIC \">1</data>'
        # target.text = "1"
        # substitution.pk = "frefntargetref193903648"
        # substitution.was = "f-ref-n-target-ref193903648"

    ### targets


def _read_book_metadata(key: KeyPath) -> dict[str, DocumentMetadata]:
    """
    Read JSON metadata stored in Elastic File System (EFS) and return a dict
    with all DocumentMetadata objects for a specific book.

    Similar to the src/builder/main/_read_book_metadata function
    """
    book_metadata: dict[str, DocumentMetadata] = {}
    # for meta_file in (key.efs_slug_dir / "_metadata").glob("**/*.json"):
    for meta_file in (key / "_metadata").glob("**/*.json"):
        with meta_file.open("r") as f:
            metadata = DocumentMetadata(meta_file)
            try:
                metadata.from_json(json.load(f))
                book_metadata[meta_file.stem] = metadata
            except KeyError as e:
                logger.info(
                    f"Invalid or obsolete metadata's Datapoint structure. Skipping "
                    f"metadata file {meta_file}. KeyError: {repr(e)}"
                )
    return book_metadata


doc = None
if __name__ == "__main__":
    doc, book_metadata = lambda_handler()
    doc.save("/tmp/efs/docx2docx/test.docx")
