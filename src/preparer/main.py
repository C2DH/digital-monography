import datetime
import pathlib
import sys
import bs4
import boto3
import json
import logging
import mammoth
import nbformat
import os
import sqlmodel
import shutil
import typing as t
import urllib.parse
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_sqs import SQSClient as boto3_SQSClient
import yaml

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
from src._common.constants import (
    ModuleEnum,
    S3Event,
    DB_URL,
    MAMMOTH_STYLE_MAP,
    IS_DEBUG,
    ASSETS_DIR,
    JB_DIR,
    DEFAULT_SFS_DIR,
    TEMP_FOOTNOTES_TABLE,
)
from src._common.models import (
    Asset,
    AssetService,
    Author,
    Book,
    Chapter,
    LinkAuthorsBooks,
)
from src._common.github_trigger import GithubTriggerMsg, GithubActionEnum
from src._common.state import DocumentState
from src._common.keys import KeyPath
from src._common.html2md import convert_to_md
from conditional_prep import is_paper_only, remove_paper_only
from citations import add_bibliography, is_citation, prepare_citations
from digital_prep import insert_digital_objects, remove_metadata_tables
from hide_metadata_in_html import hide_metadata_in_html
from prep_frontmatter import prepare_frontmatter
from metadata_extraction import prepare_metadata_tables
from remove_empty_tables import remove_empty_tables
from replace_alt_texts import is_img_with_alt_text, prepare_alt_texts
from prep_refs import is_reference, prepare_references
from ref_footnotes import (
    is_ref_footnote,
    extract_footnotes,
    prepare_refs_in_footnotes,
)
from targets import (
    is_header,
    is_caption,
    prepare_ref_targets_in_headers,
    prepare_ref_targets_in_captions,
)
from split_into_chapters import (
    split_docx_into_multiple_chapters,
    prepend_htmls_with_frontmatter,
)
from ipynb_prep import tags_to_myst_crossref_targets
from fakers import Faker


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
if IS_DEBUG:
    dynamodb = None
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")
    sqs: boto3_SQSClient = boto3.client("sqs")
db_engine = sqlmodel.create_engine(DB_URL)


def is_table(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "table")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info(f"lambda_handler. Event: {json.dumps(event, default=str)}")
    key = _get_key(event)
    event_name = _get_event_name(event)
    ####################
    ### Handle deletions
    if _is_IPYNB(key) and _is_deletion(event_name):
        _remove_fileobj(key)
        _remove_file_from_efs_domain_dirs(key)
        _remove_processed_ipynb_from_efs_chapters(key)
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.DELETE_OBJECT)
        _enqueue_to_github(msg)
        return {"statusCode": 200, "body": ""}
    if _is_DOCX(key) and _is_deletion(event_name):
        _remove_fileobj(key)
        _remove_assets_info_from_s3(key)
        # _remove_metadata_from_db(key)  # TODO: dstate
        _remove_state_from_efs(key)
        _remove_state_from_db(key)
        _remove_preprocessed_html_from_efs(key)
        _remove_html_from_s3(key)
        # _remove_processed_md_from_efs(key)
        _remove_file_from_efs_domain_dirs(key.with_suffix(".md"))
        _remove_md_from_s3(key.s3_key.with_suffix(".md"))
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.DELETE_OBJECT)
        msg_md = GithubTriggerMsg(
            key=key.s3_key.with_suffix(".md"), action=GithubActionEnum.DELETE_OBJECT
        )
        _enqueue_to_github(msg)
        _enqueue_to_github(msg_md)
        return {"statusCode": 200, "body": ""}
    if _is_deletion(event_name):
        _remove_fileobj(key)
        _remove_file_from_efs_domain_dirs(key)
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.DELETE_OBJECT)
        _enqueue_to_github(msg)
        return {"statusCode": 200, "body": ""}
    ####################################
    ### Handle updates (incl. new files)
    if _is_IPYNB(key) and _is_update(event_name):
        src = _get_source_bucket(event)
        _download_fileobj(src, key)
        _create_domain_dirs(key)
        ipynb: nbformat.NotebookNode = _unmarshall_json(key.efs_input_path)
        tags_to_myst_crossref_targets(ipynb)
        _write_processed_ipynb_to_efs_jb(ipynb, key)
        _write_processed_ipynb_to_efs_chapters(ipynb, key)
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.UPDATE_OBJECT)
        _enqueue_to_github(msg)
        # _put_to_archive_s3(key)
        return {"statusCode": 200, "body": ""}
    if _is_DOCX(key) and _is_update(event_name):
        src = _get_source_bucket(event)
        _download_fileobj(src, key)
        html_str = _convert_to_html(key.efs_input_path)
        html_soup = convert_to_bs(html_str)
        html_soup, frontmatter = prepare_frontmatter(html_soup, key)
        # print("frontmatter.myst_data", frontmatter.myst_data)
        html_soups = split_docx_into_multiple_chapters(html_soup, frontmatter)
        prepend_htmls_with_frontmatter(html_soups, frontmatter)
        footnotes = extract_footnotes(html_soup)
        for html_soup in html_soups:
            chapter: Chapter = html_soup.attrs.get("chapter")
            key = chapter.jb_key
            _create_domain_dirs(key)
            dstate = DocumentState(key)  # TODO: not key, use val from frontmatter
            dstate.__dict__[TEMP_FOOTNOTES_TABLE] = (
                footnotes  # TODO: improve syntax, del later
            )
            # print("chapter.bookmark", chapter.bookmark)
            # print("chapter.book_slug", chapter.book_slug)
            # print("chapter.chapter_slug", chapter.chapter_slug)
            # print("chapter.prefix", chapter.prefix)
            # print("chapter.fn", chapter.fn)
            # print("chapter.fm_key", chapter.fm_key)
            # print("chapter.jb_key", chapter.jb_key)
            # print("chapter.docx_key", chapter.docx_key)
            # print("-" * 75)
            dstate.add(chapter)
            # TODO: prepare_docx shouldn't have to return "state"
            html_soup, dstate, tables = prepare_docx(html_soup, dstate)
            del dstate.__dict__[TEMP_FOOTNOTES_TABLE]
            html_soup = hide_metadata_in_html(html_soup, dstate)  # last step
            # IMPORTANT NOTE: other services depend on html produced at this stage, make sure that:
            # 1) all reversible transformations are made before saving html file;
            # 2) irreversible transformations are omited to avoid not being able to recreate a book
            # as html files written at this stage will be the basis for a paper version of a book.
            html_soup = insert_digital_objects(html_soup, dstate, tables)
            html_soup = remove_metadata_tables(html_soup, dstate, tables)
            html_soup_str = str(html_soup)
            _write_assets_info_to_s3(dstate, key)
            # _write_metadata_to_db(metadata, dstate, key)  # TODO: dstate
            _write_state_to_efs(dstate, key)
            _write_state_to_db(dstate, key)
            _write_preprocessed_html_to_efs(html_soup_str, key)
            _put_html_to_s3(html_soup_str, key)
            MAYBE_HTML2MD_IN_BUILDER_AFTER_ALL_SUBSITUTIONS = """
            md = _convert_to_md(key, html_soup, dstate)
            _write_processed_md_to_efs_jb(md, key)
            _put_md_to_s3(md, key.s3_key.with_suffix(".md"))
            """
            # TODO: send to GitHub after all processing is done, just before the myst build step
            msg = GithubTriggerMsg(key=key, action=GithubActionEnum.UPDATE_OBJECT)
            _enqueue_to_github(msg)
            MAYBE_PUT_TO_GITHUB_IN_BUILDER_AFTER_ALL_SUBSITUTIONS = """
            msg_md = GithubTriggerMsg(
                key=key.s3_key.with_suffix(".md"), action=GithubActionEnum.UPDATE_OBJECT
            )
            msg_html = GithubTriggerMsg(
                key=key.s3_key.with_suffix(".html"),
                action=GithubActionEnum.UPDATE_OBJECT,
            )
            _enqueue_to_github(msg_md)
            _enqueue_to_github(msg_html)
            """
        # _put_to_archive_s3(key.s3_key.with_suffix(".md"), md)
        _log_audit_event(
            key,
            AuditStatus.SUCCESS.value,
            "Contents of the file prepared for further processing.",
        )
        return {"statusCode": 200, "body": ""}
    elif _is_CONFIG(key) and _is_update(event_name):
        src = _get_source_bucket(event)
        _download_fileobj(src, key)
        cnf = _convert_yml_to_dict(key.efs_input_path)
        project_data = _extract_project_info_from_config(cnf)
        _write_project_data_to_db(key, project_data)

        # project = cnf.get("project", {})
        # if isinstance(project, dict):
        #     title = project.get("title", "")
        #     authors = project.get("authors", [])
        #     for author in authors:
        #         if isinstance(author, dict):
        #             name = author.get("name", "")

        _create_domain_dirs(key)
        _copy_other_files_to_efs_jb(key)
        # raise NotImplementedError("Other files should also be copied to _JB")
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.UPDATE_OBJECT)
        _enqueue_to_github(msg)
        return {"statusCode": 200, "body": ""}
    elif _is_update(event_name):
        src = _get_source_bucket(event)
        _download_fileobj(src, key)
        _create_domain_dirs(key)
        _copy_other_files_to_efs_jb(key)
        # raise NotImplementedError("Other files should also be copied to _JB")
        msg = GithubTriggerMsg(key=key, action=GithubActionEnum.UPDATE_OBJECT)
        _enqueue_to_github(msg)
        return {"statusCode": 200, "body": ""}
    else:
        logger.warning(f"Event {event_name} is not supported.")
        return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    """
    Retrieves the key of the S3 object from the event, where
    "key" is the path to the file in the S3 bucket.
    """
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_event_name(event) -> t.Literal["ObjectCreated", "ObjectRemoved"]:
    try:
        event_name: str = event["Records"][0]["eventName"]
        # event_name should match "<event>:<httpMethod>" format, e.g. "ObjectCreated:Put"
        assert ":" in event_name, f"Event name {event_name} is not supported."
        event_name, _ = event_name.split(":")
        assert event_name in (
            "ObjectCreated",
            "ObjectRemoved",
        ), f"Event name {event_name} is not supported."
        return event_name
    except Exception as e:
        logger.error(f"Unable to retrieve event name. Error: {repr(e)}")
        raise


def _get_source_bucket(event) -> str:
    """
    Retrieves the source bucket name from the event. This bucket name is used to download
    the file from S3 to Elastic File System (EFS).
    """
    try:
        src = event["Records"][0]["s3"]["bucket"]["name"]
        logger.info(f"Source-bucket {src} was found in the event records.")
        return src
    except Exception as e:
        logger.error(f"Unable to retrieve the source-bucket. Error: {repr(e)}")
        raise


def _is_DOCX(key: KeyPath) -> bool:
    return key.suffix.lower() == ".docx"


def _is_IPYNB(key: KeyPath) -> bool:
    return key.suffix.lower() == ".ipynb"


def _is_CONFIG(key: KeyPath) -> bool:
    return key.suffix.lower() in [".yml", ".yaml"] and key.stem.lower() in [
        "myst",
        "_myst",
        "_config",
    ]


def _is_update(event_name: t.Literal["ObjectCreated", "ObjectRemoved"]) -> bool:
    return event_name == S3Event.OBJ_CREATED.value


def _is_deletion(event_name: t.Literal["ObjectCreated", "ObjectRemoved"]) -> bool:
    return event_name == S3Event.OBJ_REMOVED.value


def _download_fileobj(src: str, key: KeyPath) -> None:
    """
    Writes a file to Elastic File System (EFS).
    The source of the file is an S3 bucket. Name of the bucket file is read from the event.
    See more details about downloading files from s3 in the boto3 documentation:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/download_fileobj.html
    """
    try:
        # key = key.efs_filepath
        key = key.efs_input_path
        # NOTE: this commented out code shouldn't be necassary.
        # It was just a temp to fix my error when I uploaded the "assets" file instead of dir.
        key.parent.mkdir(parents=True, exist_ok=True)
        with open(key, "wb") as fileobj:
            logger.info(f"sys.getsizeof(fileobj): {str(sys.getsizeof(fileobj))}")
            s3_key = str(key.s3_key)
            logger.info(f"IS_DEBUG={IS_DEBUG}")
            logger.info(f"type(s3)={type(s3)}")
            resp = s3.download_fileobj(src, s3_key, fileobj)
            logger.info(
                f"Response from s3.download_fileobj(Bucket={src}, Key={s3_key}): "
                + json.dumps(resp, default=str)
            )
            # NOTE: This logging should be replaced with a snapshot of the directory tree.
            # for child in key.parent.iterdir():
            #     logger.info(f"File {str(child)} was found in {str(key.parent)}.")
    except Exception as e:
        logger.exception(
            f"Downloading fileobj {str(key)} from {src} failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal download.",
        )
        raise


def _remove_fileobj(key: KeyPath) -> None:
    """
    Remove a file from Elastic File System (EFS).
    """
    try:
        # key = key.efs_filepath
        key = key.efs_input_path
        if key.exists():
            logger.info(f"Stat before removal: {key.stat()}")
        key.unlink(missing_ok=True)  # remove file if it exists
        if key.exists():
            logger.info(f"Stat after removal: {key.stat()}")
        else:
            logger.info(f"File {str(key)} was removed from EFS.")
    except Exception as e:
        logger.exception(
            f"Removing fileobj {str(key)} from EFS failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal deletion from a file server.",
        )
        raise


def convert_to_bs(html_str: str) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(html_str, "html.parser")


def _create_domain_dirs(key: KeyPath) -> None:
    try:
        key.efs_jb_dir.mkdir(parents=True, exist_ok=True)
        key.efs_paper_dir.mkdir(parents=True, exist_ok=True)
        key.efs_chapters_dir.mkdir(parents=True, exist_ok=True)
        key.efs_state_dir.mkdir(parents=True, exist_ok=True)
        key.efs_warnings_dir.mkdir(parents=True, exist_ok=True)
        (key.efs_jb_dir / ASSETS_DIR).mkdir(parents=True, exist_ok=True)
        # NOTE: maybe you don't need to create assets dir in paper dir
        # just copy the whole assets dir ONLY WHEN you need to download the paper package
        # (key.efs_paper_dir / ASSETS_DIR).mkdir(parents=True, exist_ok=True)
        # NOTE: state dir does not need assets subdir
    except Exception as e:
        logger.exception(
            f"Creating directories for {str(key)} failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon creating directories in the file system.",
        )
        raise


class AuthorData(t.TypedDict):
    name: str
    orcid: str | None


class ProjectData(t.TypedDict):
    title: str
    authors: list[AuthorData]


def _extract_project_info_from_config(cnf: dict) -> ProjectData:
    project_data: ProjectData = {"title": "", "authors": []}
    # myst.yml (JBv2)
    project = cnf.get("project", {})
    if isinstance(project, dict) and project:
        project_data["title"] = project.get("title", "")
        authors = project.get("authors", [])
        for author in authors:
            if isinstance(author, dict):
                project_data["authors"].append(
                    {
                        "name": author.get("name", ""),
                        "orcid": author.get("orcid"),
                    }
                )
    # _config.yml (JBv1)
    if len(project) == 0:
        project_data["title"] = cnf.get("title", "")
        if "author" in cnf:
            project_data["authors"].append({"name": cnf["author"]})
    return project_data


def _write_project_data_to_db(key: KeyPath, project_data: ProjectData) -> None:
    try:
        with sqlmodel.Session(db_engine) as session:
            # # delete existing records for this file so there are no duplicates
            # dstate.sql_delete_by_key(session, key)
            # # write all assets included in the processed file
            # dstate.sql_insert_all(session)
            bstmt = sqlmodel.select(Book).where(Book.slug == key.slug)
            book = session.exec(bstmt).one_or_none()
            if not book:
                book = Book(
                    title=project_data["title"],
                    slug=key.slug,
                    updated=datetime.datetime.now(datetime.timezone.utc),
                )
                session.add(book)
            names_in_manuscript = [a["name"] for a in project_data["authors"]]
            orcids_in_manuscript = [a.get("orcid") for a in project_data["authors"]]
            if len(names_in_manuscript) == len(orcids_in_manuscript):
                astmt = (
                    sqlmodel.select(Author)
                    .where(sqlmodel.col(Author.orcid).in_(orcids_in_manuscript))
                    .where(sqlmodel.col(Author.name).in_(names_in_manuscript))
                )
            else:
                # if there is at least one author without ORCID, match only by name
                astmt = sqlmodel.select(Author).where(
                    sqlmodel.col(Author.name).in_(names_in_manuscript)
                )
            authors = session.exec(astmt).all()
            names_in_db = [author.name for author in authors]
            for a in project_data["authors"]:
                if a["name"] not in names_in_db:
                    author = Author(name=a["name"], orcid=a.get("orcid"), books=[book])
                    session.add(author)
            session.commit()
        logger.info(f"Sent SQL INSERT cmd for {key} without an error.")
        return
    except Exception as e:
        logger.exception(
            f"Writing {key.slug} config data to the database failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing config data to the database.",
        )
        raise


def prepare_docx(
    html_soup: bs4.BeautifulSoup,
    dstate: DocumentState,
) -> tuple[bs4.BeautifulSoup, DocumentState, list[bs4.element.Tag]]:
    # TODO: pass bs instead of str
    images_with_alttxt = []
    tables = []
    headers = []
    captions = []
    citations = []
    ref_footnotes = []
    # target_footnotes = []
    references = []
    paper_only = []
    dstate.metadata.char_count, dstate.metadata.word_count = _get_char_and_word_count(
        html_soup
    )
    classifiers = [
        (is_img_with_alt_text, images_with_alttxt),
        (is_citation, citations),
        (is_table, tables),
        (is_header, headers),
        (is_caption, captions),
        (is_reference, references),
        (is_ref_footnote, ref_footnotes),
        # (is_target_footnote, target_footnotes),
        (is_paper_only, paper_only),
        # is_ref_footnote, is_target_footnote, prepare_refs_in_footnotes, prepare_targets_in_footnotes
    ]
    """
    Before applying the processing, this subprocedure traverses the tree
    recursively and puts relevant bs4 objects (html elements) inside 
    respective lists. Processing is then applied on the marked elements.
    """
    for node in html_soup.descendants:
        for check_if_meets_criteria, container in classifiers:
            if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
                container.append(node)
    html_soup, bibliography = prepare_citations(html_soup, dstate, citations)
    html_soup = add_bibliography(html_soup, bibliography)
    html_soup = prepare_ref_targets_in_headers(html_soup, dstate, headers)
    html_soup = prepare_ref_targets_in_captions(html_soup, dstate, captions)
    # html_soup = prepare_targets_in_footnotes(html_soup, dstate, target_footnotes)
    # html_soup = prepare_ref_targets_in_footnotes(html_soup,dstate, footnotes)
    html_soup = prepare_refs_in_footnotes(html_soup, dstate, ref_footnotes)
    # with open(f"/tmp/efs/output_{dstate.key.name}.html", "w", encoding="utf-8") as f:
    #     f.write(str(html_soup))
    html_soup = prepare_references(html_soup, dstate, references)
    html_soup = prepare_metadata_tables(html_soup, dstate, tables)
    html_soup = remove_paper_only(html_soup, dstate, paper_only)
    html_soup = remove_empty_tables(html_soup, dstate, tables)
    html_soup = prepare_alt_texts(html_soup, dstate, images_with_alttxt)
    return html_soup, dstate, tables


def _get_char_and_word_count(html_soup: bs4.BeautifulSoup) -> tuple[int, int]:
    soup_contents_list: list[str] = []
    for elem in html_soup.find_all(text=True):
        if isinstance(elem, bs4.element.PageElement):
            soup_contents_list.append(elem.text.strip())
    soup_contents = "".join(soup_contents_list).replace(" ", "")  # minimize spaces
    words = []
    for line in soup_contents_list:
        for word in line.split(" "):
            if word and not word.isspace():
                words.append(word)
    return len(soup_contents), len(words)


def _convert_to_html(key: KeyPath) -> str:
    try:
        with open(key, "rb") as f:
            result = mammoth.convert_to_html(f, style_map=MAMMOTH_STYLE_MAP)
            logger.info(f"Converting {key} to html succedded.")
            return result.value
    except Exception as e:
        logger.exception(f"Converting {key} to html failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon preparing html.",
        )
        raise


def _convert_yml_to_dict(key: KeyPath) -> dict:
    try:
        with open(key, "rb") as f:
            cnf = yaml.safe_load(f)
            if not isinstance(cnf, dict):
                cnf = {}
            logger.info(f"Unmarshalling {key} config succeeded.")
            return cnf
    except Exception as e:
        logger.exception(f"Unmarshalling {key} config failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon unmarshalling config yaml.",
        )
        raise


def _convert_to_md(
    key: KeyPath,
    html_soup: bs4.BeautifulSoup,
    dstate: DocumentState,
) -> str:
    try:
        return convert_to_md(html_soup, dstate)
    except Exception as e:
        logger.exception(f"Converting to md failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon preparing markdown.",
        )
        raise


def _put_object(body: bytes, dst: str, key: KeyPath) -> t.Any:
    try:
        # TODO: do I have to encode and decode contents?
        resp = s3.put_object(Body=body.decode("utf-8"), Bucket=dst, Key=str(key))
        logger.info(
            f"Response from s3.put_object(Bucket={dst}, Key={key}): "
            + json.dumps(resp, default=str)
        )
        return resp
    except Exception as e:
        logger.exception(f"Put object {key} to bucket {dst} failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal synchronization.",
        )
        raise


def _remove_html_from_s3(key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".html")
        bucket = os.environ["IR_APKG_HTML_BUCKET_NAME"]
        resp = s3.delete_object(Bucket=bucket, Key=str(s3_key))
        logger.info(
            f"Response from s3.put_object(Bucket={bucket}, Key={s3_key}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Deleting html from s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal html synchronization.",
        )
        raise


def _put_html_to_s3(contents: str, key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".html")
        _put_object(
            contents.encode("utf-8"),
            os.environ.get("IR_APKG_HTML_BUCKET_NAME", ""),
            s3_key,
        )
    except Exception as e:
        logger.exception(f"Putting html to s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal html synchronization.",
        )
        raise


def _remove_md_from_s3(key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".md")
        bucket = os.environ["IR_APKG_MD_BUCKET_NAME"]
        resp = s3.delete_object(Bucket=bucket, Key=str(s3_key))
        logger.info(
            f"Response from s3.put_object(Bucket={bucket}, Key={s3_key}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Deleting md from s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal html synchronization.",
        )
        raise


def _put_md_to_s3(contents: str, key: KeyPath) -> None:
    try:
        _put_object(
            contents.encode("utf-8"),
            os.environ.get("IR_APKG_MD_BUCKET_NAME", ""),
            key,
        )
    except Exception as e:
        logger.exception(f"Putting md to s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon internal markdown synchronization.",
        )
        raise


def _enqueue_to_github(msg: GithubTriggerMsg) -> None:
    try:
        # msg = GithubTriggerMsg(key=key, action=GithubActionEnum.UPDATE_OBJECT)
        logger.info(
            f"_queue_to_trigger_github(key={msg.key}, action={msg.action.value})"
        )
        aws_account_region = os.environ.get("AWS_ACCOUNT_REGION", "")
        aws_account_id = os.environ.get("AWS_ACCOUNT_ID", "")
        sqs_github_trigger = os.environ.get("SQS_GITHUB_FIFO_TRIGGER_NAME", "")
        QueueUrl = f"https://sqs.{aws_account_region}.amazonaws.com/{aws_account_id}/{sqs_github_trigger}"
        logger.info(
            f"Attempting to call sqs.send_message(QueueUrl={QueueUrl}, MessageBody={msg.dumps()}, MessageDeduplicationId={msg.deduplication_id()}, MessageGroupId={msg.slug})"
        )
        resp = sqs.send_message(
            QueueUrl=QueueUrl,
            MessageBody=msg.dumps(),
            MessageDeduplicationId=msg.deduplication_id(),
            MessageGroupId=msg.slug,
        )
        logger.info(
            f"Response from sqs.send_message(QueueUrl={QueueUrl}, MessageBody={msg.dumps()}, MessageDeduplicationId={msg.deduplication_id()}, MessageGroupId={msg.slug}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Putting file to Github failed. Error: {repr(e)}")
        _log_audit_event(
            msg.key,
            AuditStatus.FAILED.value,
            "Error upon saving to GitHub.",
        )
        raise


# def _put_to_archive_s3(key: KeyPath, contents: t.Optional[str] = None) -> None:
#     try:
#         logger.info(f"_put_to_archive_s3(key={key}, contents={contents})")
#         if contents is None:
#             try:
#                 with open(key.efs_filepath, "r") as f:
#                     contents = f.read()
#             except UnicodeDecodeError as e:
#                 with open(key.efs_filepath, "rb") as f:
#                     contents = f.read().decode("utf-8", "ignore")
#         _put_object(
#             contents.encode("utf-8"),
#             ARCHIVE_APKG_ALL,
#             key.s3_key,
#         )
#     except Exception as e:
#         logger.exception(f"Putting file to archive s3 bucket failed. Error: {repr(e)}")
#         _log_audit_event(
#             key,
#             AuditStatus.FAILED.value,
#             "Error upon archiving.",
#         )
#         raise


def _remove_preprocessed_html_from_efs(key: KeyPath) -> None:
    try:
        new_efs_filepath = key.efs_chapters_path.with_suffix(".html")
        new_efs_filepath.unlink(missing_ok=True)
        logger.info(f"{new_efs_filepath} was removed from EFS.")
    except Exception as e:
        logger.exception(
            f"Deleting pre-processed html from /efs failed. Error: {repr(e)}"
        )
        raise


def _write_preprocessed_html_to_efs(html: str, key: KeyPath) -> None:
    try:
        new_efs_filepath = key.efs_chapters_path.with_suffix(".html")
        new_efs_filepath.parent.mkdir(exist_ok=True)
        with open(new_efs_filepath, "w") as f:
            f.write(html)
    except Exception as e:
        logger.exception(f"Writing pre-processed html to /efs failed. Error: {repr(e)}")
        raise


def _remove_file_from_efs_domain_dirs(key: KeyPath) -> None:
    try:
        key.efs_jb_path.unlink(missing_ok=True)
        key.efs_paper_path.unlink(missing_ok=True)
        key.efs_state_path.unlink(missing_ok=True)
        key.efs_input_path.unlink(missing_ok=True)
        key.efs_warnings_path.unlink(missing_ok=True)
        logger.info(f"{str(key.efs_jb_path)} was removed from EFS.")
    except Exception as e:
        logger.exception(
            f"Deleting file from {DEFAULT_SFS_DIR}/{JB_DIR} failed. Error: {repr(e)}"
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


def _remove_assets_info_from_s3(key: KeyPath) -> None:
    try:
        s3_key = AssetService.get_s3_key(key)
        bucket = os.environ.get("METADATA_ASSETS_BUCKET_NAME", "")
        resp = s3.delete_object(Bucket=bucket, Key=s3_key)
        logger.info(
            f"Response from s3.delete_object(Bucket={bucket}, Key={s3_key}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(
            f"Deleting assets info from s3 bucket failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon removing assets info from docs.",
        )
        raise


def _write_assets_info_to_s3(docstate: DocumentState, key: KeyPath) -> None:
    try:
        s3_key = AssetService.get_s3_key(key)
        bucket = os.environ.get("METADATA_ASSETS_BUCKET_NAME", "")
        assets: list[Asset] = docstate["assets"]
        body = json.dumps([ass.model_dump(mode="json") for ass in assets], default=str)
        resp = s3.put_object(Body=body, Bucket=bucket, Key=s3_key)
        logger.info(
            f"Response from s3.put_object(Bucket={bucket}, Key={s3_key}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Putting assets info to s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing assets info from docs.",
        )
        raise


def _remove_state_from_efs(key: KeyPath) -> None:
    try:
        fp = key.efs_state_path.with_suffix(".json")
        fp.unlink(missing_ok=True)  # remove file if it exists
        logger.info(f"Chapter state was removed from {str(fp)}")
    except Exception as e:
        logger.exception(
            f"Removing chapter state in json from /efs directory failed. Error: {repr(e)}"
        )
        raise


def _write_state_to_efs(docstate: DocumentState, key: KeyPath) -> None:
    try:
        # json_data = metadata.to_json() # TODO: DocumentMetadata should be depracated
        fp = key.efs_state_path.with_suffix(".json")
        with open(fp, "w") as f:
            json.dump(docstate.to_dict(), f)
        logger.info(f"Chapter state was saved to {str(fp)}")
    except Exception as e:
        logger.exception(
            f"Writing chapter state in json to /efs directory failed. Error: {repr(e)}"
        )
        raise


def _remove_state_from_db(docstate: DocumentState, key: KeyPath) -> None:
    try:
        with sqlmodel.Session(db_engine) as session:
            docstate.sql_delete_by_key(session, key)
        logger.info(f"Sent SQL DELETE cmd for {key} without an error.")
        return
    except Exception as e:
        logger.exception(f"Removing records from the database failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon removing records from the database.",
        )
        raise


def _write_state_to_db(dstate: DocumentState, key: KeyPath) -> None:
    try:
        with sqlmodel.Session(db_engine) as session:
            # delete existing records for this file so there are no duplicates
            dstate.sql_delete_by_key(session, key)
            # write all assets included in the processed file
            dstate.sql_insert_all(session)
        logger.info(f"Sent SQL INSERT cmd for {key} without an error.")
        return
    except Exception as e:
        logger.exception(f"Writing records to the database failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing records to the database.",
        )
        raise


def _write_processed_ipynb_to_efs_jb(
    ipynb: nbformat.NotebookNode, key: KeyPath
) -> None:
    # NOTE: this writes directly to _JB, which assumes no further processing is needed
    if key.parts[-2] != ".ipynb_checkpoints":
        nbformat.write(ipynb, key.efs_jb_path)


def _write_processed_ipynb_to_efs_chapters(
    ipynb: nbformat.NotebookNode, key: KeyPath
) -> None:
    # NOTE: this writes to _CHAPTERS for eventual processing
    if key.parts[-2] != ".ipynb_checkpoints":
        nbformat.write(ipynb, key.efs_chapters_path)


def _remove_processed_ipynb_from_efs_chapters(key: KeyPath) -> None:
    try:
        # fp = key.efs_slug_metadata_path.parent / key.github_path.with_suffix(".json")
        fp = key.efs_chapters_path
        fp.unlink(missing_ok=True)  # remove file if it exists
        logger.info(f"Pre-processed ipynb was removed from {str(fp)}")
    except Exception as e:
        logger.exception(
            f"Removing pre-processed ipynb from /efs directory failed. Error: {repr(e)}"
        )
        raise


def _unmarshall_json(key: KeyPath) -> nbformat.NotebookNode:
    """
    Read a Jupyter notebook from a file and return the nbformat.NotebookNode object.
    """
    with open(key, "r") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)
    return nb


def _copy_other_files_to_efs_jb(key: KeyPath) -> None:
    try:
        if not key.efs_jb_path.parent.exists():
            key.efs_jb_path.parent.mkdir(parents=True)
        shutil.copy2(key.efs_input_path, key.efs_jb_path)
        logger.info(
            f"File {str(key.efs_input_path)} was copied to {str(key.efs_jb_path)}"
        )
    except Exception as e:
        logger.exception(
            f"Copying file to {DEFAULT_SFS_DIR}/{JB_DIR} failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon copying non-manuscript file to the file server.",
        )
        raise


def _log_audit_event(key: KeyPath, status: int, msg: str) -> None:
    event = AuditEvent(
        slug=key.slug,
        module=ModuleEnum.PREPARER.value,
        filename=key.name,
        status=status,
        msg=msg,
    )
    event.send(dynamodb)
    if status == AuditStatus.FAILED.value:
        alert = AlertLog(slug=key.slug, status=AlertStatus.FAIL.value)
        alert.send(dynamodb)
    logger.info(f"Audit event logged: {event}")
