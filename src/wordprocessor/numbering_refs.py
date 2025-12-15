import collections
import docx
import docx.document
import docx.text.hyperlink
import docx.text.paragraph

from src._common.constants import AUTONUMBER_PLACEHOLDER
from src._common.models import Chapter, RefTarget, Target, TargetService
from src._common.state import BookState, DocumentState
from src._common.keys import KeyPath


def prepare_refs(
    key: KeyPath,
    doc: docx.document.Document,
    bookstate: BookState,
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
    _update_hyperlink_texts(key, doc, bookstate)


def update_targets_for_substitutions(bookstate: BookState) -> None:
    """
    In order to do reference numbering correctly,
    first we have to update "target.new_item_num" property.

    To do that, group all targets by fm_key.
    Then, order targets by prev_item_num within each group
    and call _update_state_records_for_substitution() for each group.
    """
    grouped_targets = collections.defaultdict(list)
    all_targets: list[Target] = bookstate.all("targets")
    for target in all_targets:
        grouped_targets[target.fm_key].append(target)

    for group in grouped_targets.values():
        group: list[Target] = sorted(group, key=lambda t: (t.prev_item_num or 0))
        _update_state_records_for_substitution(group)


def _update_state_records_for_substitution(
    datapoints: list[Target],
) -> None:
    """
    This function is similar (but not identic) to
    "builderv3/.../_update_state_records_for_substitution()".
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
        if dp.is_paper == False:
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
    bookstate: BookState,
) -> None:
    for link in p.hyperlinks:
        target = _find_target(key, link, bookstate)
        if target is not None:
            _replace_link_text(link, target)


def _find_target(
    key: KeyPath,
    link: docx.text.hyperlink.Hyperlink,
    bookstate: dict[str, DocumentState],
) -> Target | None:
    ref_targets: list[RefTarget] = bookstate.all("ref_targets")
    target_ids: set[str] = {
        rt.target_id for rt in ref_targets if rt.fragment == link.fragment
    }
    if len(target_ids) == 0:
        return None
    elif len(target_ids) == 1:
        target_id = target_ids.pop()
        target = bookstate.get("targets", target_id, attrib="hash")
        return target
    elif len(target_ids) > 1 and link.address:
        # there is link.address, therefore target is in different file as ref
        target_file_stem = link.address.split(".")[0]
        targets: list[Target] = bookstate.all("targets")
        targets_with_fragment = [t for t in targets if t.hash in target_ids]
        for t in targets_with_fragment:
            if t.loc.stem == target_file_stem:
                return t
        raise NotImplementedError(
            "Figure out how to filter the right target based on `link.address`."
        )
    elif len(target_ids) > 1 and not link.address:
        # no link.address, therefore target is in the same file as ref
        targets: list[Target] = bookstate.all("targets")
        for t in targets:
            if t.hash in target_ids and t.fm_key == key:
                return t
        raise NotImplementedError(
            "Figure out how to filter the right target WITHOUT the `link.address`."
        )
    raise NotImplementedError("Need to think it thgrough more carefully.")


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
