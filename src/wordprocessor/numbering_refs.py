import docx
import docx.document
import docx.text.hyperlink
import docx.text.paragraph

try:
    from constants import AUTONUMBER_PLACEHOLDER
    from metadata import DocumentMetadata, TargetDatapoint
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .constants import AUTONUMBER_PLACEHOLDER  # type: ignore
    from .metadata import DocumentMetadata, TargetDatapoint  # type: ignore
    from .keys import KeyPath


def prepare_refs(
    key: KeyPath,
    doc: docx.document.Document,
    book_metadata: dict[str, DocumentMetadata],
) -> None:
    """
    In a reference, replace placeholder {{AUTONUMBER_PLACEHOLDER}}
    with the updated number of the target.

    For example,
    <w:hyperlink r:id="rId12" w:anchor="figRedSquare" w:history="1">
        <w:r w:rsidR="00255759">
            <w:rPr>
                <w:rStyle w:val="Hyperlink"/>
            </w:rPr>
            <w:t>Figure {{AUTONUMBER_PLACEHOLDER}}</w:t>
        </w:r>
    </w:hyperlink>
    """
    for metadata in book_metadata.values():
        _update_datapoints_for_targets(metadata.targets)
    _update_hyperlink_texts(key, doc, book_metadata)


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
    key: KeyPath,
    doc: docx.document.Document,
    book_metadata: dict[str, DocumentMetadata],
) -> None:
    for p in doc.paragraphs:
        _update_hyperlink_texts_in_paragraph(key, p, book_metadata)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _update_hyperlink_texts_in_paragraph(key, p, book_metadata)


def _update_hyperlink_texts_in_paragraph(
    key: KeyPath,
    p: docx.text.paragraph.Paragraph,
    book_metadata: dict[str, DocumentMetadata],
) -> None:
    for link in p.hyperlinks:
        if AUTONUMBER_PLACEHOLDER in link.text and link.address:
            target_file_stem = link.address.split(".")[0]
            target = _find_target(link, target_file_stem, book_metadata)
            _replace_link_text(link, target)
        elif AUTONUMBER_PLACEHOLDER in link.text and link.fragment:
            target = _find_target(link, key.stem, book_metadata)
            _replace_link_text(link, target)


def _find_target(
    link: docx.text.hyperlink.Hyperlink,
    stem: str,
    book_metadata: dict[str, DocumentMetadata],
) -> TargetDatapoint | None:
    try:
        return next(
            t for t in book_metadata[stem].targets if t.fragment == link.fragment
        )
    except StopIteration:
        return None


def _replace_link_text(
    link: docx.text.hyperlink.Hyperlink, target: TargetDatapoint
) -> None:
    for run in link.runs:
        if (
            AUTONUMBER_PLACEHOLDER in run.text
            and target.is_paper == False
            and target.is_digital == True
        ):
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, "")
        elif AUTONUMBER_PLACEHOLDER in run.text:
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, target.new_value())
