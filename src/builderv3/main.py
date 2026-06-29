# NOTE: consider renaming from "builder", this is more book level aggregator and merger.
# "preparer" microservice works per document, this prepares on a book level.
import collections
import boto3
import bs4
import datetime
import json
import logging
import os
import pathlib
import re
import sqlmodel
import sys
import shutil
import typing as t
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client


# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import (
    ASSETS_DIR,
    AUTONUMBER_PLACEHOLDER,
    DB_URL,
    IS_DEBUG,
    ModuleEnum,
)
from src._common.models import (
    Chapter,
    RefService,
    RefTarget,
    Target,
    TargetService,
)
from src._common.html2md import convert_to_md
from src._common.keys import KeyPath
from src._common.state import BookState
from fakers import Faker
from prep_config import init_myst_config


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_builder.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)


if IS_DEBUG:
    dynamodb = None  # TODO: add fakers
    s3 = Faker("s3")
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")
db_engine = sqlmodel.create_engine(DB_URL)


def lambda_handler(event, context) -> None:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = _get_key(event)
    _log_audit_event(key, AuditStatus.PENDING.value, "Building book has started.")
    _copy_assets(key)
    _copy_manuscript(key)
    bookstate = _load_book_state(key)
    _init_myst_config(key, bookstate)
    update_targets_for_substitutions(bookstate)
    print("\n\nbookstate.config", bookstate.config, "\n\n")
    # enrich_html_from_docx(key, bookstate)
    for key in sorted(key.efs_chapters_dir.glob("**/*")):
        assert key.suffix.lower() in (".html", ".ipynb")
        with open(key, "r") as f:
            filestr = f.read()
        if key.suffix.lower() == ".ipynb":
            pass  # TODO: handle ipynb files
        elif key.suffix.lower() == ".html":
            jb_key = key.efs_jb_path.with_suffix(".md")
            chapter: Chapter = bookstate.get("chapters", jb_key, attrib="jb_key")
            fm_key = chapter.fm_key if chapter else None

            html_soup = bs4.BeautifulSoup(filestr, "html.parser")
            _update_references(fm_key, html_soup, bookstate)
            md = _convert_to_md(key, html_soup, bookstate)
            md = _replace_placeholders_with_new_values(md, bookstate)
            _write_processed_md_to_efs_jb(md, key)
            _write_processed_html_to_efs(str(html_soup), key)

    # enqueue_to_github
    # build book <== no
    # distribute book <== no
    _log_audit_event(key, AuditStatus.SUCCESS.value, "Building book in progress...")
    # update refs in db
    # verify book
    # save warnings
    logging.info("Builder Lambda function finished.")
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        slug = event["Records"][0]["body"]
        pth = pathlib.Path(slug) / "_config.yml"
        return KeyPath(pth)
    except Exception as e:
        logging.exception(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _copy_assets(key: KeyPath) -> None:
    try:
        src = key.efs_slug_dir / ASSETS_DIR
        dst = key.efs_jb_dir / ASSETS_DIR
        dst.mkdir(parents=True, exist_ok=True)
        logging.info(f"Copying files from {src} to {dst}.")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        # cmd = ["cp", "-r", src, dst]
        # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # p.wait()
    except Exception as e:
        logging.exception(f"Unable to copy assets. Error: {repr(e)}")
        _log_audit_event(key, AuditStatus.FAILED.value, "Error while copying assets.")
        raise


def _copy_manuscript(key: KeyPath) -> None:
    for md in key.efs_slug_dir.glob("**/*.md"):
        _copy_file_to_jb_dir(md)
    for ipynb in key.efs_slug_dir.glob("**/*.ipynb"):
        _copy_file_to_jb_dir(ipynb)


def _copy_file_to_jb_dir(src: KeyPath) -> None:
    try:
        relative_path = src.relative_to(src.efs_slug_dir)
        dst = src.efs_jb_dir / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        logger.info(f"Copied {src} to {dst}.")
    except Exception as e:
        logger.exception(f"Unable to copy file {src} to {dst}. Error: {repr(e)}")
        _log_audit_event(
            src, AuditStatus.FAILED.value, f"Error while copying chapter {src}."
        )
        raise


def _load_book_state(key: KeyPath) -> BookState:
    try:
        return BookState(key)
    except Exception as e:
        logging.exception(f"Loading book state failed. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while loading book state."
        )
        raise


def _init_myst_config(key: KeyPath, bookstate: BookState) -> None:
    """
    Read and update "myst.yml" config file.
    """
    try:
        init_myst_config(key, bookstate)
        logger.info(f"Successfully initialized myst config file.")
    except Exception as e:
        logging.exception(
            f'Initializing "myst.yml" config file failed. Error: {repr(e)}'
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while initializing Jupyter Book config file.",
        )
        raise


def _update_references(
    fm_key: KeyPath, html_soup: bs4.BeautifulSoup, bookstate: BookState
) -> None:
    anchors = html_soup.find_all("a", href=True)
    for a_tag in anchors:
        assert isinstance(a_tag, bs4.Tag)
        target = _find_target(fm_key, a_tag, bookstate)
        if target:
            a_tag["href"] = "#" + target.hash
            # TODO: remove "was" if not used
            was, a_tag.string = _new_link_text(a_tag, target, bookstate)


def update_targets_for_substitutions(bookstate: BookState) -> None:
    """
    In order to do reference numbering correctly,
    first we have to update "target.new_item_num" property.

    To do that, group all targets by loc_key (key after split).
    Then, order targets by prev_item_num within each group
    and call _update_datapoints_for_targets() for each group.
    """
    if bookstate.config and bookstate.config.dgtmon.per_chapter_numbering:
        sorted_targets = _group_and_sort_targets_by_chapter(bookstate)
        for group in sorted_targets.values():
            _update_state_records_for_substitution(group)
    else:
        sorted_targets = _sort_all_targets(bookstate)
        for t in sorted_targets:
            # No file count prefix when autonumbering accross the whole book.
            t.file_count = None
        _update_state_records_for_substitution(sorted_targets)


def _sort_all_targets(
    bookstate: BookState,
) -> list[Target]:
    """
    Ordering when we can to increment autonumbering across the whole book, not by chapters.
    Sort all targets in a bookstate first by file count and then by number in that file.
    E.g. Fig 1 in file 02_chpt2.docx should be AFTER Fig 2 in file 01_chpt1.docx.
    """

    def _get_file_count(t: Target) -> int | None:
        return t.file_count

    all_targets: list[Target] = sorted(bookstate.all("targets"), key=_get_file_count)
    return sorted(all_targets, key=lambda t: (t.prev_item_num or 0))


def _group_and_sort_targets_by_chapter(
    bookstate: BookState,
) -> collections.OrderedDict[int, list[Target]]:
    """
    Ordering when we can to increment autonumbering by chapters.
    To do that, group all targets by loc_key (key after split).
    Then, order targets by prev_item_num within each group.
    """
    grouped_and_sorted_targets: collections.OrderedDict[int, list[Target]] = (
        collections.OrderedDict()
    )
    grouped_targets: dict[int, list[Target]] = collections.defaultdict(list)

    def _get_file_count(t: Target) -> int | None:
        return t.file_count

    all_targets: list[Target] = sorted(bookstate.all("targets"), key=_get_file_count)
    for target in all_targets:
        assert (
            target.file_count is not None
        ), "Autonumbering relies on file_count. Check if file name is prepended with a number or find some other method."
        grouped_targets[target.file_count].append(target)

    for group in grouped_targets.values():
        # NOTE: this assumes target counting is consistent accross chapters
        # In reality, a book might be made out of 2 files that have to be splited
        # into multiple chapters, each with its own autonumbering.
        # Thus, relying on `t.prev_item_num` alone is not sufficient.
        # In that case, consider adding new `item_num` attrib to Target,
        # taken from incremental numbering done in "preparer/targets.py".
        group: list[Target] = sorted(group, key=lambda t: (t.prev_item_num or 0))
        if len(group) > 0:
            assert (
                group[0].file_count is not None
            ), "Return key can be None only if autonumbering is not by chapters"
            grouped_and_sorted_targets[group[0].file_count] = group
    return grouped_and_sorted_targets


def _update_state_records_for_substitution(
    datapoints: list[Target],
) -> None:
    """
    This function is similar (but not identic) to
    "wordprocessor/numbering_refs/_update_datapoints_for_targets()".
    Especially note that we omit when dp.is_digital == False.
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
        assert isinstance(dp, Target)
        if dp.item_type == "ref":
            assert (
                dp.prev_item_num is None
            ), "Check assumption that in every ref prev_item_num is None"
            pass
        elif dp.is_digital == False:
            # increment omitted count
            ommited_count[dp.item_type] += 1
        elif dp.prev_item_num is not None:
            # update "new_item_num" property
            dp.new_item_num = prev_item_num[dp.item_type] + 1
            prev_item_num[dp.item_type] += 1


def _find_target(
    src_key: KeyPath, a_tag: bs4.Tag, bookstate: BookState
) -> Target | None:
    """
    Looks for a reference target so that reference's href and text
    can be synced with updated value of the target.
    This is not needed for external links (e.g to http or mailto)
    and footnotes, in which case the system should return "None".
    If no ref target was found, href and text of a reference shouldn't be updated.
    """
    fn, fragment = _get_fn_and_fragment_from_href(a_tag["href"])
    ref_targets: list[RefTarget] = bookstate.filter(
        "ref_targets", fragment, attrib="fragment"
    )
    if len(ref_targets) > 1 and not fn:
        assert (
            len([rt for rt in ref_targets if rt.fm_key == src_key]) == 1
        ), "Expected one rt with the same fragment per fm_key"
        ref_target = next(rt for rt in ref_targets if rt.fm_key == src_key)
        return bookstate.get("targets", ref_target.target_id, "hash")
    elif len(ref_targets) > 1:
        raise NotImplementedError("Strange case. Investigate.")
    elif len(ref_targets) == 1:
        ref_target = ref_targets[0]
        return bookstate.get("targets", ref_target.target_id, "hash")
    elif len(ref_targets) == 0 and a_tag["href"].startswith("#footnote-"):
        # just a footnote
        return None
    elif len(ref_targets) == 0 and RefService.is_external(a_tag["href"]):
        # just external link
        return None
    return None


def _new_link_text(
    a_tag: bs4.Tag, target: Target, bookstate: BookState
) -> tuple[str, str]:
    """
    Link text to be placed in `[text](...)` syntax.
    Returns replaced text and the new text.
    """
    replace_with = TargetService.to_digital_version(target)
    text_to_replace = ""
    tag_text = a_tag.text
    if AUTONUMBER_PLACEHOLDER in tag_text:
        text_to_replace = AUTONUMBER_PLACEHOLDER
        tag_text = tag_text.replace(text_to_replace, replace_with)
        return text_to_replace, tag_text
    match = _match_complex_numbering(tag_text)
    if isinstance(match, re.Match):
        start, end = match.span(1)
        text_to_replace = tag_text[start:end]
        return text_to_replace, tag_text.replace(text_to_replace, replace_with)
    elif replace_with == "" and target.item_type == "heading":
        return text_to_replace, tag_text
    else:  # maybe check if tag_href == "#target_hash"
        to_replace = target.text
        tag_text = tag_text.replace(to_replace, replace_with)
        text_to_replace = to_replace
        return text_to_replace, tag_text


def _match_complex_numbering(tag_text: str) -> re.Match | None:
    """
    Search for complex numbering in the text of the anchor tag.
    Complex number pattern is either `<roman_num><sep><digit>` (e.g. 'iv.1')
    or `<letter of the alphabet><sep><digit>` (e.g. 'a.1') or `<digit><sep><digit>`.
    This solution assumes the alphabetical numbering will not be greater than 'z' (26).
    Accepted separators match MS Word separators: '.:—-'
    """
    before = r"(?:\s)"  # make sure starts with a whitespace
    heading_number = r"([ivxlcdm]+|[a-z]{1}|\d+)"
    sep = r"[.:—-]{1}"
    pattern = rf"{before}({heading_number}{sep}\d)"
    assert pattern == r"(?:\s)(([ivxlcdm]+|[a-z]{1}|\d+)[.:—-]{1}\d)"
    return re.search(pattern, tag_text.lower())
    # r"(?:\s)(([ivxlcdm]+|[a-z]{1}|\d+)[.:—-]{1}\d)", tag_text.lower()


def _replace_placeholders_with_new_values(md: str, bookstate: BookState) -> str:
    """
    Replace target placeholders in markdown files with new values.

    Before:
    ```md
    (1ecb9f4f0fe2e53d)=
    **Figure {{ 1ecb9f4f0fe2e53d }}:** Some image.
    ```

    After:
    ```md
    (1ecb9f4f0fe2e53d)=
    **Figure 1.1:** Some image.
    ```
    """
    targets: list[Target] = bookstate.all("targets")
    for target in targets:
        placeholder = r"{{ " + target.hash + r" }}"
        if placeholder not in md:
            continue
        md = md.replace(
            placeholder,
            TargetService.to_digital_version(target),
        )
    return md


def _convert_to_md(
    key: KeyPath,
    html_soup: bs4.BeautifulSoup,
    bookstate: BookState,
) -> str:
    try:
        return convert_to_md(html_soup, bookstate.all_records)
    except Exception as e:
        logger.exception(f"Converting to md failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon preparing markdown.",
        )
        raise


def _write_processed_md_to_efs_jb(md: str, key: KeyPath) -> None:
    try:
        new_efs_filepath = key.efs_jb_path.with_suffix(".md")
        with open(new_efs_filepath, "w") as f:
            f.write(md)
    except Exception as e:
        logger.exception(f"Writing md to /efs failed. Error: {repr(e)}")
        raise


def _write_processed_html_to_efs(html: str, key: KeyPath) -> None:
    """
    Update html with information gathered from all chapters consisting of a whole book.
    """
    try:
        new_efs_filepath = key.efs_chapters_path.with_suffix(".html")
        with open(new_efs_filepath, "w") as f:
            f.write(html)
    except Exception as e:
        logger.exception(f"Writing processed html to /efs failed. Error: {repr(e)}")
        raise


def _get_fn_and_fragment_from_href(href: str) -> tuple[str, str]:
    """
    Extracts filename and fragment identifier from an URI.
    If a value is not present, an empty string is returned instead.

    E.g. "manuscript.docx" and "fragment" from:
        "https://sharepoint.com/some/path/manuscript.docx#fragment"
        "./manuscript.docx#fragment"
    """
    # 'A fragment identifier component is indicated by the presence of a number sign ("#")'
    # so it should always be an index of #.
    # See https://www.rfc-editor.org/rfc/rfc3986#section-3.5
    if "#" in href:
        fragment_idx = href.index("#")
    else:
        fragment_idx = len(href)
    path = href[:fragment_idx]
    fragment = href[fragment_idx + 1 :]
    if "." not in path:
        return "", fragment
    for scheme in ["tel:", "mailto:", "sms:", "javascript:"]:
        if path.startswith(scheme):
            return "", fragment
    if "/" not in path:
        return path, fragment
    filename = ""
    for i in range(len(path) - 1, -1, -1):
        ch = path[i]
        # if ch == ".":
        #     suffix = path[i + 1 :]
        if ch == "/":
            filename = path[i + 1 :]
            break
    if "." not in filename:
        return "", fragment
    return filename, fragment


RESTORE_FOR_SAVING_WARNINGS = """
def _put_json_to_s3(key: KeyPath, warnings: list[dict[str, str]]) -> None:
    try:
        warnings_grouped: dict[str, list[dict[str, str]]] = {}
        for w in warnings:
            if w.get("fn") not in warnings_grouped:
                warnings_grouped[w.get("fn")] = []
            warnings_grouped[w.get("fn")].append(w)

        for fn, warnings in warnings_grouped.items():
            s3_key = key.slug + "/" + fn.split(".")[0] + ".json"
            body = json.dumps(warnings, default=str)
            bucket = os.environ.get("VERIFIER_MSGS", "")
            resp = s3.put_object(Body=body, Bucket=bucket, Key=str(s3_key))
            logger.info(
                f"Response from s3.put_object(Bucket={bucket}, Key={str(s3_key)}): "
                + json.dumps(resp, default=str)
            )
    except Exception as e:
        logger.exception(f"Putting json to s3 bucket failed. Error: {repr(e)}")
        raise
"""


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.BUILDER.value,
        filename="",
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.FAILED.value:
        alert = AlertLog(slug=key.slug, status=AlertStatus.FAIL.value)
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")
