# NOTE : this is not as much builder, as
# book level preparer (preparer works per document)
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
    File,
    FileService,
    Ref,
    RefService,
    RefTarget,
    Substitution,
    SubstitutionService,
    Target,
)
from src._common.html2md import convert_to_md
from src._common.keys import KeyPath
from src._common.state import BookState, DocumentState, read_book_metadata
from fakers import Faker
from prep_config import create_myst_config_file


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
    _create_myst_config_file(key)
    # enrich_html_from_docx(key, bookstate)

    for key in sorted(key.efs_chapters_dir.glob("**/*")):
        assert key.suffix.lower() in (".html", ".ipynb")
        with open(key, "r") as f:
            filestr = f.read()
        if key.suffix.lower() == ".ipynb":
            pass  # TODO: handle ipynb files
        elif key.suffix.lower() == ".html":
            jb_key = key.efs_jb_path.with_suffix(".md")
            # docstate_idontthinkineedit = (
            #     bookstate[jb_key] if jb_key in bookstate else DocumentState(jb_key)
            # )
            # chapter_idontthinkineedit: Chapter | None = (
            #     docstate_idontthinkineedit.first("chapters")
            # )
            chapter: Chapter = bookstate.get("chapters", jb_key, attrib="jb_key")
            # from which docx file this file was created
            # assert chapter == chapter_idontthinkineedit
            fm_key = chapter.fm_key if chapter else None

            html_soup = bs4.BeautifulSoup(filestr, "html.parser")
            anchors = html_soup.find_all("a", href=True)
            ref_targets: list[RefTarget] = bookstate.all("ref_targets")
            for a_tag in anchors:
                assert isinstance(a_tag, bs4.Tag)
                fn, fragment = _get_fn_and_fragment_from_href(a_tag["href"])
                # find target()
                ref_targets = bookstate.filter(
                    "ref_targets", fragment, attrib="fragment"
                )
                target: Target | None = None
                if len(ref_targets) > 1 and not fn:
                    # No target file, hence target is in the same file as ref
                    assert (
                        len([rt for rt in ref_targets if rt.fm_key == fm_key]) == 1
                    ), "Expected one rt with the same fragment per fm_key"
                    ref_target = next(rt for rt in ref_targets if rt.fm_key == fm_key)
                    target = bookstate.get("targets", ref_target.target_id, "hash")
                elif len(ref_targets) > 1:
                    raise NotImplementedError("Strange case. Investigate.")
                elif len(ref_targets) == 1:
                    ref_target = ref_targets[0]
                    target = bookstate.get("targets", ref_target.target_id, "hash")
                elif len(ref_targets) == 0 and a_tag["href"].startswith("#footnote-"):
                    pass  # just a footnote
                elif len(ref_targets) == 0 and RefService.is_external(a_tag["href"]):
                    pass  # just external link
                else:
                    pass
                    # print(a_tag)
                print("-" * 75)
                #########################################
                if target:
                    a_tag["href"] = "#" + target.hash
                    new_value = _find_new_value(target, bookstate)
                    was, a_tag.string = _new_link_text(a_tag, target, new_value)

        # Do I have all the data I need in the state files?
        # If not, do I have to iterate over all chapters twice?
        md = _convert_to_md(key, html_soup, bookstate)
        # md = _replace_placeholders_with_new_values(md, bookstate)
        _write_processed_md_to_efs_jb(md, key)
        _write_processed_html_to_efs(str(html_soup), key)

    # _connect_refs_and_targets(key, bookstate)
    # _html2md
    # _make_substitutions(key, bookstate)
    # enqueue_to_github

    # build book <== no
    # distribute book <== no
    _log_audit_event(key, AuditStatus.SUCCESS.value, "Building book in progress...")
    # connect assets to refs_to_assets
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
        bookstate = BookState()
        bookstate.load_from_file(key)
        bookstate.merge_docstate(key)
        return bookstate
    except Exception as e:
        logging.exception(f"Loading book state failed. Error: {repr(e)}")
        _log_audit_event(
            key, AuditStatus.FAILED.value, "Error while loading book state."
        )
        raise


def _create_myst_config_file(key: KeyPath) -> None:
    """
    Write "myst.yml" config file for Jupyter Book v2 build.
    """
    try:
        create_myst_config_file(key)
        logger.info(f"Successfully created myst config file.")
    except Exception as e:
        logging.exception(f'Creating "myst.yml" config file failed. Error: {repr(e)}')
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while creating Jupyter Book config file.",
        )
        raise


def _new_link_text(a_tag: bs4.Tag, target: Target, new_value: str) -> tuple[str, str]:
    # def _new_link_text(a_tag: bs4.Tag, target: Target) -> tuple[str, str]:
    """
    Link text to be placed in `[text](...)` syntax.
    Returns replaced text and the new text.
    """
    text_to_replace = ""
    tag_href = a_tag["href"]
    tag_text = a_tag.text
    target_hash = target.hash
    if AUTONUMBER_PLACEHOLDER in tag_text:
        text_to_replace = AUTONUMBER_PLACEHOLDER
        replace_with = new_value
        # replace_with = r"{{ " + target_hash + r" }}"
        tag_text = tag_text.replace(text_to_replace, replace_with)
        return text_to_replace, tag_text
    THIS_CASE_NEVER_HAPPENS = """
    # at this stage, both infile and f2f look like `#some-hash`
    if RefService.is_internal_f2f(tag_href):
        to_replace = ""
        for i in range(len(tag_text)):
            if tag_text[i].isdigit():
                to_replace += tag_text[i]
            if to_replace and not tag_text[i].isdigit():
                break
        replace_with = new_value
        # replace_with = r"{{ " + target_hash + r" }}"
        if to_replace:
            tag_text = tag_text.replace(to_replace, replace_with)
        text_to_replace = to_replace
    """
    match = _match_complex_numbering(tag_text)
    if isinstance(match, re.Match):
        start, end = match.span(1)
        text_to_replace = tag_text[start:end]
        replace_with = new_value
        # replace_with = r"{{ " + target_hash + r" }}"
        return text_to_replace, tag_text.replace(text_to_replace, replace_with)
    elif new_value == "" and target.item_type == "heading":
        return text_to_replace, tag_text
    else:  # maybe check if tag_href == "#target_hash"
        to_replace = target.text
        replace_with = new_value
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


def _find_new_value(target: Target, bookstate: BookState) -> str:
    subst: Substitution | None = bookstate.get(
        "substitutions", target.hash, attrib="hash"
    )
    if not isinstance(subst, Substitution):
        return ""
        # return "xxxNEWVALUE_BUT_NO_SUBSTITUTION_FOUNDxxx"
    # file_prefix = FileService.get_number_from_filename(file.stem)
    # file_prefix = target.file_count
    file_prefix = subst.file_count if subst else None
    return SubstitutionService.to_digital_version(subst, file_prefix)


def _replace_placeholders_with_new_values(md: str, bookstate: BookState) -> None:
    """
    Replace substitution placeholders in markdown files with new values.
    """
    substitutions: list[Substitution] = bookstate.all("substitutions")
    for subs in substitutions:
        md = md.replace(
            r"{{ " + subs.pk + r" }}",
            SubstitutionService.to_digital_version(subs, subs.file_count),
        )
    return md


def _make_substitutions(key: KeyPath, bookstate: BookState) -> None:
    """
    Replace substitution placeholders in markdown files with new values.

    I don't like this implementation because it should be done for .md and .ipynb
    by JupyterBook. Also, I don't like having too many slow IO operations.
    However, I needed some solution fast and I didn't have time to fight with JupyterBook.
    I couldn't make JupyterBook to do the substitutions for f2f refs.
    """
    for md in key.efs_jb_dir.glob("*.md"):
        dstate = bookstate.get(md.stem)
        try:
            if md.stem not in bookstate:
                continue
            with open(md, "r") as f:
                mdstr = f.read()
                # Make mapping of file_count to file prefix.
                # This is suboptimal, but FileDatapoint only knows file stem and prefix.
                # I could add more data to it, but since user has to correctly
                # write this data in yaml file by hand, the less data the better :/
                file_prefices: dict[int, str] = {}
                files: list[File] = dstate["files"]
                for file in files:
                    file_count = FileService.get_number_from_filename(file.stem)
                    file_prefices[file_count] = file.prefix
                # Replace placeholders with new values, incl. file prefix
                substitutions: list[Substitution] = dstate["substitutions"]
                for subs in substitutions:
                    if subs.file_count in file_prefices:
                        file_prefix = file_prefices[subs.file_count]
                    else:
                        file_prefix = None
                    mdstr = mdstr.replace(
                        r"{{ " + subs.pk + r" }}",
                        SubstitutionService.to_digital_version(subs, file_prefix),
                    )
                    # NOTE: seems to just repeat "was" attr
            # post_mdstr = mdstr
            # if pre_mdstr != post_mdstr:
            #     diff = difflib.ndiff(
            #         pre_mdstr.splitlines(keepends=True),
            #         post_mdstr.splitlines(keepends=True),
            #     )
            #     print("".join(diff), end="")
            with open(md, "w") as f:
                f.write(mdstr)
        except Exception as e:
            logger.exception(f"Replacing placeholders in {md} failed. Error: {repr(e)}")
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Error upon updating automatic numbering.",
            )


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


def _connect_refs_and_targets(key: KeyPath, bookstate: BookState) -> None:
    # iterate over chapters
    # traverse html soups
    # find all refs, I assume paper-only has been removed
    # iterate over refs, find targets in bookstate
    # I assume target numbers have been updated
    # update ref string with up-to-date target number
    # update ref href

    # For the targets, maybe just a simple operation to
    # replace all HASH with updated strings?
    pass


def _make_substitutions(key: KeyPath, bookstate: BookState) -> None:
    """
    Replace substitution placeholders in markdown files with new values.

    I don't like this implementation because it should be done for .md and .ipynb
    by JupyterBook. Also, I don't like having too many slow IO operations.
    However, I needed some solution fast and I didn't have time to fight with JupyterBook.
    I couldn't make JupyterBook to do the substitutions for f2f refs.
    """
    for md in key.efs_jb_dir.glob("*.md"):
        print(f"Making substitutions in {md}.")
        print(bookstate.docstates.keys())
        dstate = bookstate.docstates.get(md.stem, None)
        print("dstate", dstate.__dict__.keys() if dstate else None)

    # THIS_IS_HOW_IT_WAS_IN_JB1 = """
    book_metadata = read_book_metadata(key)
    for md in key.efs_slug_dir.glob("*.md"):
        dstate = book_metadata.get(md.stem)
        try:
            if md.stem not in book_metadata:
                continue
            with open(md, "r") as f:
                mdstr = f.read()
                # Make mapping of file_count to file prefix.
                # This is suboptimal, but FileDatapoint only knows file stem and prefix.
                # I could add more data to it, but since user has to correctly
                # write this data in yaml file by hand, the less data the better :/
                file_prefices: dict[int, str] = {}
                files: list[File] = dstate["files"]
                for file in files:
                    file_count = FileService.get_number_from_filename(file.stem)
                    file_prefices[file_count] = file.prefix
                # Replace placeholders with new values, incl. file prefix
                substitutions: list[Substitution] = dstate["substitutions"]
                for subs in substitutions:
                    if subs.file_count in file_prefices:
                        file_prefix = file_prefices[subs.file_count]
                    else:
                        file_prefix = None
                    mdstr = mdstr.replace(
                        r"{{ " + subs.pk + r" }}",
                        SubstitutionService.to_digital_version(subs, file_prefix),
                    )
                    # NOTE: seems to just repeat "was" attr
            with open(md, "w") as f:
                f.write(mdstr)
        except Exception as e:
            logger.exception(f"Replacing placeholders in {md} failed. Error: {repr(e)}")
            _log_audit_event(
                key,
                AuditStatus.FAILED.value,
                "Error upon updating automatic numbering.",
            )
    # """


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
