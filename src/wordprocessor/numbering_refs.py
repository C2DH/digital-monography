import docx
import docx.document
import docx.text.hyperlink
import docx.text.paragraph

from src._common.constants import AUTONUMBER_PLACEHOLDER
from src._common.models import Chapter, RefTarget, Target, TargetService
from src._common.state import BookState, DocumentState
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
    _update_datapoints_for_targets(bookstate.all("targets"))
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
    bookstate: BookState,
) -> None:
    for link in p.hyperlinks:
        print("-" * 50)
        target = _find_target(key, link, bookstate)
        print("link.address", link.address)
        print("link.fragment", link.fragment)
        print("link.text", link.text)
        print("target", target)
        print("-" * 50)
        if target is not None:
            _replace_link_text(link, target)

        # if AUTONUMBER_PLACEHOLDER in link.text and link.address:
        #     print("link.text", link.text)
        #     print("link.address", link.address)
        #     target_file_stem = link.address.split(".")[0]
        #     target = _find_target(link, target_file_stem, bookstate)
        #     if target is not None:
        #         _replace_link_text(link, target)
        # elif AUTONUMBER_PLACEHOLDER in link.text and link.fragment:
        #     print("link.text", link.text)
        #     print("link.fragment", link.fragment)
        #     fn = input_key.name if hasattr(input_key, "name") else ""
        #     fn = input_key.name
        #     target = _find_target(link, fn, bookstate)
        #     if target is not None:
        #         _replace_link_text(link, target)


def _find_target(
    key: KeyPath,
    link: docx.text.hyperlink.Hyperlink,
    bookstate: dict[str, DocumentState],
) -> Target | None:
    # print("-" * 50)
    # if AUTONUMBER_PLACEHOLDER in link.text:
    # print("=" * 50)

    ref_targets: list[RefTarget] = bookstate.all("ref_targets")
    target_ids: set[str] = {
        rt.target_id for rt in ref_targets if rt.fragment == link.fragment
    }
    print("len(target_ids)", len(target_ids))
    if len(target_ids) == 0:
        return None
    elif len(target_ids) == 1:
        target_id = target_ids.pop()
        print("target_id", target_id)
        target = bookstate.get("targets", target_id, attrib="hash")
        print("target", target)
        return target
    elif len(target_ids) > 1 and link.address:
        print("link.address", link.address)
        # there is link.address, therefore target is in different file as ref
        target_file_stem = link.address.split(".")[0]
        targets: list[Target] = bookstate.all("targets")
        targets_with_fragment = [t for t in targets if t.hash in target_ids]
        assert len(targets_with_fragment) > 0, "There should be at least one target."
        for t in targets_with_fragment:
            if t.loc.stem == target_file_stem:
                return t
        raise NotImplementedError(
            "Figure out how to filter the right target based on `link.address`."
        )
    elif len(target_ids) > 1 and not link.address:
        # no link.address, therefore target is in the same file as ref
        print("elif len(target_ids) > 1 and not link.address")
        targets: list[Target] = bookstate.all("targets")
        for t in targets:
            # print("---")
            # print(t)
            # print("---")
            # print("key", key)
            # print("t.fm_key", t.fm_key)
            # print("t.loc", t.loc)
            # print("link.fragment", link.fragment)
            # print("link.text", link.text)
            if t.hash in target_ids and t.fm_key == key:
                return t
        raise NotImplementedError(
            "Figure out how to filter the right target WITHOUT the `link.address`."
        )

    raise NotImplementedError("Need to think it thgrough more carefully.")
    # targets_with_fragment = [t for t in targets if t.fragment == link.fragment]
    # targets: list[Target] = bookstate.all("targets")
    # print('bookstate.len("targets")', bookstate.len("targets"))
    # print("link.fragment", link.fragment)
    # print("link.address", link.address)
    # print("link.text", link.text)
    # # for t in targets:
    # #     print("t.fragment", t.fragment)
    # targets_with_fragment = [t for t in targets if t.fragment == link.fragment]
    # print("targets_with_fragment", targets_with_fragment, len(targets_with_fragment))
    # if len(targets_with_fragment) == 0:
    #     return None
    # elif len(targets_with_fragment) == 1:
    #     return targets_with_fragment[0]
    # elif len(targets_with_fragment) > 1:
    #     target_file_stem = link.address.split(".")[0]
    #     for t in targets_with_fragment:
    #         if t.loc.stem == target_file_stem:
    #             return t
    #     raise NotImplementedError(
    #         "Figure out how to filter the right target based on `link.address`."
    #     )


def _replace_link_text(
    link: docx.text.hyperlink.Hyperlink,
    target: Target,
) -> None:
    for run in link.runs:
        print("run.text", run.text)
        if (
            AUTONUMBER_PLACEHOLDER in run.text
            and target.is_paper == False
            and target.is_digital == True
        ):
            print("BEFORE run.text", run.text)
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, "")
        elif AUTONUMBER_PLACEHOLDER in run.text:
            print("BEFORE run.text", run.text)
            new_value = TargetService.to_paper_version(target)
            print("new_value", new_value)
            run.text = run.text.replace(AUTONUMBER_PLACEHOLDER, new_value)
            print("AFTER run.text", run.text)
