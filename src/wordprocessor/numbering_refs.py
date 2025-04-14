import docx
import docx.document
import docx.text.hyperlink
import docx.text.paragraph

try:
    # from constants import CAPTION_ALLOWED_ITEMS
    from metadata import DocumentMetadata, TargetDatapoint
except (ImportError, ModuleNotFoundError):
    # from .constants import CAPTION_ALLOWED_ITEMS  # type: ignore
    from .metadata import DocumentMetadata, TargetDatapoint  # type: ignore


def prepare_refs(
    doc: docx.document.Document, book_metadata: dict[str, DocumentMetadata]
) -> None:
    """
    In a reference, replace placeholder "XXX" with the updated number of the target.

    For example,
    <w:hyperlink r:id="rId12" w:anchor="figRedSquare" w:history="1">
        <w:r w:rsidR="00255759">
            <w:rPr>
                <w:rStyle w:val="Hyperlink"/>
            </w:rPr>
            <w:t>Figure XXX</w:t>
        </w:r>
    </w:hyperlink>
    """
    for metadata in book_metadata.values():
        _update_datapoints_for_targets(metadata.targets)
    _update_hyperlink_texts(doc, book_metadata)


def _update_datapoints_for_targets(
    datapoints: list[TargetDatapoint],
) -> None:
    """
    This function is similar (but not identic) to
    "preparer/substitutions_prep/update_datapoints_for_targets()".
    Especially note that we omit when dp.is_paper == False.
    """
    prev_item_num = {
        "heading": 0,
        "equation": 0,
        "figure": 0,
        "table": 0,
        "": 0,
    }
    ommited_count = {
        "heading": 0,
        "equation": 0,
        "figure": 0,
        "table": 0,
        "": 0,
    }
    for dp in datapoints:
        if dp.is_paper == False and prev_item_num is not None:
            val = 0 if prev_item_num[dp.item_type] == dp.prev_item_num else 1
            ommited_count[dp.item_type] += val
        elif dp.prev_item_num is not None:
            dp.new_item_num = dp.prev_item_num - ommited_count[dp.item_type]
        prev_item_num[dp.item_type] = dp.prev_item_num


def _update_hyperlink_texts(
    doc: docx.document.Document, book_metadata: dict[str, DocumentMetadata]
) -> None:
    for p in doc.paragraphs:
        _update_hyperlink_texts_in_paragraph(p, book_metadata)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _update_hyperlink_texts_in_paragraph(p, book_metadata)


def _update_hyperlink_texts_in_paragraph(
    p: docx.text.paragraph.Paragraph, book_metadata: dict[str, DocumentMetadata]
) -> None:
    for link in p.hyperlinks:
        if "XXX" in link.text and link.address:
            target = _find_target(link, book_metadata)
            _replace_link_text(link, target)


def _find_target(
    link: docx.text.hyperlink.Hyperlink, book_metadata: dict[str, DocumentMetadata]
) -> TargetDatapoint | None:
    target_file_stem = link.address.split(".")[0]
    try:
        return next(
            t
            for t in book_metadata[target_file_stem].targets
            if t.fragment == link.fragment
        )
    except StopIteration:
        return None


def _replace_link_text(
    link: docx.text.hyperlink.Hyperlink, target: TargetDatapoint
) -> None:
    for run in link.runs:
        if "XXX" in run.text and target.is_paper == False and target.is_digital == True:
            run.text = run.text.replace(
                "XXX",
                f"({target.item_type} {target.new_value()} in the digital version)",
            )
        elif "XXX" in run.text:
            run.text = run.text.replace("XXX", target.new_value())
