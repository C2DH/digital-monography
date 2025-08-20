import docx
import docx.document
import docx.text.hyperlink
import docx.text.paragraph

from src._common.constants import AUTONUMBER_PLACEHOLDER
from src._common.models import Target, TargetService
from src._common.state import DocumentState
from src._common.keys import KeyPath

# try:
#     from constants import AUTONUMBER_PLACEHOLDER
#     from models import Target, TargetService
#     from state import DocumentState
#     from keys import KeyPath
# except (ImportError, ModuleNotFoundError):
#     from .constants import AUTONUMBER_PLACEHOLDER  # type: ignore
#     from .models import Target, TargetService  # type: ignore
#     from .state import DocumentState  # type: ignore
#     from .keys import KeyPath  # type: ignore


def prepare_refs(
    key: KeyPath,
    doc: docx.document.Document,
    bookstate: dict[str, DocumentState],
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
    for docstate in bookstate.values():
        _update_datapoints_for_targets(docstate["targets"])
    _update_hyperlink_texts(key, doc, bookstate)


def _update_datapoints_for_targets(
    datapoints: list[Target],
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
    bookstate: dict[str, DocumentState],
) -> None:
    for p in doc.paragraphs:
        _update_hyperlink_texts_in_paragraph(key, p, bookstate)


def _update_hyperlink_texts_in_paragraph(
    key: KeyPath,
    p: docx.text.paragraph.Paragraph,
    bookstate: dict[str, DocumentState],
) -> None:
    for link in p.hyperlinks:
        if AUTONUMBER_PLACEHOLDER in link.text and link.address:
            target_file_stem = link.address.split(".")[0]
            target = _find_target(link, target_file_stem, bookstate)
            if target is not None:
                _replace_link_text(link, target)
        elif AUTONUMBER_PLACEHOLDER in link.text and link.fragment:
            stem = key.stem if hasattr(key, "stem") else ""
            target = _find_target(link, stem, bookstate)
            if target is not None:
                _replace_link_text(link, target)


def _find_target(
    link: docx.text.hyperlink.Hyperlink,
    stem: str,
    bookstate: dict[str, DocumentState],
) -> Target | None:
    targets: list[Target] = bookstate[stem]["targets"]
    return next((t for t in targets if t.fragment == link.fragment), None)


def _replace_link_text(
    link: docx.text.hyperlink.Hyperlink,
    target: Target,
) -> None:
    for run in link.runs:
        if (
            AUTONUMBER_PLACEHOLDER in run.text
            and target.is_paper == False
            and target.is_digital == True
        ):
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, "")
        elif AUTONUMBER_PLACEHOLDER in run.text:
            new_value = TargetService.to_paper_version(target)
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, new_value)
