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
import typing as t
import urllib.parse

from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_dynamodb.client import DynamoDBClient as boto3_DynamoDBClient

try:
    from audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from conditional_rendering import is_paper_only, remove_paper_only
    from constants import (
        ModuleEnum,
        # ARCHIVE_APKG_ALL,
        AWS_ACCOUNT_REGION,
        AWS_ACCOUNT_ID,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        MAMMOTH_STYLE_MAP,
        METADATA_ASSETS_BUCKET_NAME,
        SQS_GITHUB_FIFO_TRIGGER_NAME,
        IS_DEBUG,
        #
        FIELD_DIGITAL_SOURCE,
        DEFAULT_SFS_DIR,
    )
    from citations import add_bibliography, is_citation, prepare_citations
    from digital_prep import insert_digital_objects, remove_metadata_tables
    from hide_metadata_in_html import hide_metadata_in_html
    from metadata import DocumentMetadata, AssetDatapoint
    from metadata_extraction import prepare_metadata_tables
    from remove_empty_tables import remove_empty_tables
    from replace_alt_texts import is_img_with_alt_text, prepare_alt_texts
    from refs import (
        prepare_ref_targets_in_headers,
        prepare_ref_targets_in_captions,
        prepare_ref_targets_in_footnotes,
        prepare_references,
        is_header,
        is_caption,
        is_footnote,
        is_reference,
    )
    from substitutions_prep import count_targets_for_substitutions
    from html2md import convert_to_md
    from ipynb_prep import tags_to_myst_crossref_targets
    from keys import KeyPath
    from fakers import Faker
except (ImportError, ModuleNotFoundError):
    from .audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from .conditional_rendering import is_paper_only, remove_paper_only
    from .constants import (
        ModuleEnum,
        # ARCHIVE_APKG_ALL,
        AWS_ACCOUNT_REGION,
        AWS_ACCOUNT_ID,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        MAMMOTH_STYLE_MAP,
        METADATA_ASSETS_BUCKET_NAME,
        SQS_GITHUB_FIFO_TRIGGER_NAME,
        IS_DEBUG,
        #
        FIELD_DIGITAL_SOURCE,
        DEFAULT_SFS_DIR,
    )
    from .citations import add_bibliography, is_citation, prepare_citations
    from .digital_prep import insert_digital_objects, remove_metadata_tables
    from .hide_metadata_in_html import hide_metadata_in_html
    from .metadata import DocumentMetadata, AssetDatapoint
    from .metadata_extraction import prepare_metadata_tables
    from .remove_empty_tables import remove_empty_tables
    from .replace_alt_texts import is_img_with_alt_text, prepare_alt_texts
    from .refs import (
        prepare_ref_targets_in_headers,
        prepare_ref_targets_in_captions,
        prepare_ref_targets_in_footnotes,
        prepare_references,
        is_header,
        is_caption,
        is_footnote,
        is_reference,
    )
    from .substitutions_prep import count_targets_for_substitutions
    from .html2md import convert_to_md
    from .ipynb_prep import tags_to_myst_crossref_targets
    from .keys import KeyPath
    from .fakers import Faker

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


FIXED_SUBSTITUTIONS = {
    "01_a___Ref177042490": "1",
    "01_a___Ref177044323": "1",
    "02_b.docx#02_b__tblSimpleTable": "2",
    "02_b.docx#02_b__h1HyperlinksB": "1",
}


if IS_DEBUG:
    dynamodb = None
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    dynamodb: boto3_DynamoDBClient = boto3.resource("dynamodb")
    s3: boto3_S3Client = boto3.client("s3")
    sqs = boto3.client("sqs")


def is_table(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "table")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info(f"lambda_handler. Event: {json.dumps(event, default=str)}")
    key = _get_key(event)
    metadata = DocumentMetadata(key)
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    if key.suffix.lower() == ".ipynb":
        ipynb: nbformat.NotebookNode = _unmarshall_json(key.efs_filepath)
        tags_to_myst_crossref_targets(ipynb)
        _write_processed_ipynb_to_efs(ipynb, key)
        _enqueue_to_github(key)
        # _put_to_archive_s3(key)
        return {"statusCode": 200, "body": ""}
    if key.suffix.lower() == ".docx":
        html_str = _convert_to_html(key.efs_filepath)
        html_soup, metadata, tables = prepare_docx(html_str, metadata)
        # images_with_alttxt = []
        # tables = []
        # headers = []
        # captions = []
        # citations = []
        # footnotes = []
        # references = []
        # paper_only = []
        # html_str = _convert_to_html(key.efs_filepath)
        # html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        # metadata.char_count, metadata.word_count = _get_char_and_word_count(html_soup)
        # classifiers = [
        #     (is_img_with_alt_text, images_with_alttxt),
        #     (is_citation, citations),
        #     (is_table, tables),
        #     (is_header, headers),
        #     (is_caption, captions),
        #     (is_footnote, footnotes),
        #     (is_reference, references),
        #     (is_paper_only, paper_only),
        # ]
        # """
        # Before applying the processing, this subprocedure traverses the tree
        # recursively and puts relevant bs4 objects (html elements) inside
        # respective lists. Processing is then applied on the marked elements.
        # """
        # for node in html_soup.descendants:
        #     for check_if_meets_criteria, container in classifiers:
        #         if isinstance(node, bs4.element.Tag) and check_if_meets_criteria(node):
        #             container.append(node)
        # html_soup, bibliography = prepare_citations(html_soup, metadata, citations)
        # html_soup = add_bibliography(html_soup, bibliography)
        # html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        # html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        # html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        # html_soup = prepare_references(html_soup, metadata, references)
        # html_soup = prepare_metadata_tables(html_soup, metadata, tables)
        # html_soup = remove_paper_only(html_soup, metadata, paper_only)
        # html_soup = remove_empty_tables(html_soup, metadata, tables)
        # html_soup = prepare_alt_texts(html_soup, metadata, images_with_alttxt)
        # html_soup = count_targets_for_substitutions(html_soup, metadata)
        # ########################

        logger.info("====================================")
        logger.info(f"Looking for {FIELD_DIGITAL_SOURCE}")
        logger.info(f"metadata.filepath.parent: ({metadata.filepath.parent})")
        # root = pathlib.Path(DEFAULT_SFS_DIR) / metadata.filepath.parent
        # metadata = compute_additional_metadata_fields(metadata)
        html_soup = hide_metadata_in_html(html_soup, metadata)  # last step
        html_soup_str = str(html_soup)
        # IMPORTANT NOTE: other services depend on html produced at this stage, make sure that:
        # 1) all reversible transformations are made before saving html file;
        # 2) irreversible transformations are omited to avoid not being able to recreate a book
        # as html files written at this stage will be the basis for a paper version of a book.
        html_soup = insert_digital_objects(html_soup, metadata, tables)
        html_soup = remove_metadata_tables(html_soup, metadata, tables)
        _write_config_to_efs(metadata, key)

        # for rec in getattr(metadata, "assets"):
        #     for k, v in rec.to_json().items():
        #         print(">", k, v, type(v))
        # logger.info(
        #     f"==Metadata: "
        #     + json.dumps([rec.to_json() for rec in getattr(metadata, "assets")], default=str)
        # )
        _write_assets_info_to_s3(metadata, key)
        _write_metadata_to_db(metadata, key)
        _write_metadata_to_efs(metadata, key)
        _write_processed_html_to_efs(html_soup_str, key)
        _put_html_to_s3(html_soup_str, key)
        md = _convert_to_md(key, html_soup, metadata)
        _write_processed_md_to_efs(md, key)
        _put_md_to_s3(md, key.s3_key.with_suffix(".md"))
        _enqueue_to_github(key)
        _enqueue_to_github(key.s3_key.with_suffix(".md"))
        # _put_to_archive_s3(key.s3_key.with_suffix(".md"), md)
        _log_audit_event(
            key,
            AuditStatus.SUCCESS.value,
            "Contents of the file prepared for further processing.",
        )
        return {"statusCode": 200, "body": ""}
    else:

        # _write_to_efs(key) # <=============
        _enqueue_to_github(key)
        return {"statusCode": 200, "body": ""}


def _get_key(event) -> KeyPath:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        return KeyPath(key_str)
    except Exception as e:
        logger.error(f"Unable to retrieve object key. Error: {repr(e)}")
        raise


def _get_source_bucket(event) -> str:
    try:
        src = event["Records"][0]["s3"]["bucket"]["name"]
        logger.info(f"Source-bucket {src} was found in the event records.")
        return src
    except Exception as e:
        logger.error(f"Unable to retrieve the source-bucket. Error: {repr(e)}")
        raise


def _download_fileobj(src: str, key: KeyPath) -> None:
    try:
        key = key.efs_filepath
        # temp to remove the "assets" file
        assets_dir = pathlib.Path("/mnt/efs/{key.slug}/assets")
        if assets_dir.exists() and not assets_dir.is_dir() and assets_dir.is_file():
            assets_dir.unlink()
        # end temp
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
            for child in key.parent.iterdir():
                logger.info(f"File {str(child)} was found in {str(key.parent)}.")
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


def prepare_docx(
    html_str: str, metadata: DocumentMetadata
) -> tuple[bs4.BeautifulSoup, DocumentMetadata, list[bs4.element.Tag]]:
    images_with_alttxt = []
    tables = []
    headers = []
    captions = []
    citations = []
    footnotes = []
    references = []
    paper_only = []
    # html_str = _convert_to_html(key.efs_filepath)
    html_soup = bs4.BeautifulSoup(html_str, "html.parser")
    metadata.char_count, metadata.word_count = _get_char_and_word_count(html_soup)
    classifiers = [
        (is_img_with_alt_text, images_with_alttxt),
        (is_citation, citations),
        (is_table, tables),
        (is_header, headers),
        (is_caption, captions),
        (is_footnote, footnotes),
        (is_reference, references),
        (is_paper_only, paper_only),
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
    html_soup, bibliography = prepare_citations(html_soup, metadata, citations)
    html_soup = add_bibliography(html_soup, bibliography)
    html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
    html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
    html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
    html_soup = prepare_references(html_soup, metadata, references)
    html_soup = prepare_metadata_tables(html_soup, metadata, tables)
    html_soup = remove_paper_only(html_soup, metadata, paper_only)
    html_soup = remove_empty_tables(html_soup, metadata, tables)
    html_soup = prepare_alt_texts(html_soup, metadata, images_with_alttxt)
    html_soup = count_targets_for_substitutions(html_soup, metadata)
    return html_soup, metadata, tables


def _get_char_and_word_count(html_soup: bs4.BeautifulSoup) -> tuple[int, int]:
    soup_contents_list = []
    for elem in html_soup.find_all(text=True):
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


def _convert_to_md(
    key: KeyPath, html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata
) -> str:
    try:
        return convert_to_md(html_soup, metadata)
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


def _enqueue_to_github(key: KeyPath) -> None:
    try:
        key_str = str(key)
        logger.info(f"_queue_to_trigger_github(key={key_str})")
        aws_account_region = os.environ.get("AWS_ACCOUNT_REGION", "")
        aws_account_id = os.environ.get("AWS_ACCOUNT_ID", "")
        sqs_github_trigger = os.environ.get("SQS_GITHUB_FIFO_TRIGGER_NAME", "")
        QueueUrl = f"https://sqs.{aws_account_region}.amazonaws.com/{aws_account_id}/{sqs_github_trigger}"
        MessageBody = key_str
        MessageDeduplicationId = key_str
        MessageGroupId = key.slug
        resp = sqs.send_message(
            QueueUrl=QueueUrl,
            MessageBody=MessageBody,
            MessageDeduplicationId=MessageDeduplicationId,
            MessageGroupId=MessageGroupId,
        )
        logger.info(
            f"Response from sqs.send_message(QueueUrl={QueueUrl}, MessageBody={MessageBody}, MessageDeduplicationId={MessageDeduplicationId}, MessageGroupId={MessageGroupId}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Putting file to archive s3 bucket failed. Error: {repr(e)}")
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon archiving.",
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


def _write_config_to_efs(metadata: DocumentMetadata, key: KeyPath) -> None:
    # new_efs_filepath = key.efs_filepath.with_suffix(".yml")
    # substitutions = {subs.placeholder: subs.was for subs in metadata.substitutions}
    # TODO: set config for a particular file
    pass


def _write_processed_html_to_efs(html: str, key: KeyPath) -> None:
    new_efs_filepath = key.efs_slug_html_path.with_suffix(".html")
    new_efs_filepath.parent.mkdir(exist_ok=True)
    with open(new_efs_filepath, "w") as f:
        f.write(html)


def _write_processed_md_to_efs(md: str, key: KeyPath) -> None:
    new_efs_filepath = key.efs_filepath.with_suffix(".md")
    with open(new_efs_filepath, "w") as f:
        f.write(md)


def _write_assets_info_to_s3(metadata: DocumentMetadata, key: KeyPath) -> None:
    try:
        s3_key = AssetDatapoint.get_s3_key(key)
        bucket = os.environ.get("METADATA_ASSETS_BUCKET_NAME", "")
        body = json.dumps([ass.to_json() for ass in metadata.assets], default=str)
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


def _write_metadata_to_db(metadata: DocumentMetadata, key: KeyPath) -> None:
    if dynamodb is None:
        return
    try:
        tables = {
            "assets": os.environ.get("DYNAMODB_ASSETS_TBL", ""),
            "citation_groups": os.environ.get("DYNAMODB_CITATIONS_TBL", ""),
            "headings": os.environ.get("DYNAMODB_HEADINGS_TBL", ""),
            # "warnings": DYNAMODB_WARNINGS_TBL,
        }
        for domain, tbl in tables.items():
            table = dynamodb.Table(tbl)
            resp = table.put_item(
                Item={
                    "slug": key.slug,
                    "fn": key.name,
                    "records": [rec.to_json() for rec in getattr(metadata, domain)],
                }
            )
            logger.info(
                f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
            )

        return
    except Exception as e:
        logger.exception(
            f"Writing metadata in json to database failed. Error: {repr(e)}"
        )
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error upon writing metadata to database.",
        )
        raise


def _write_metadata_to_efs(metadata: DocumentMetadata, key: KeyPath) -> None:
    try:
        json_data = metadata.to_json()
        fp = key.add_to_efs_slug_dir("_metadata").parent / key.github_path.with_suffix(
            ".json"
        )
        logger.info(f"File: {fp}")
        logger.info(f"Meta: {json.dumps(json_data)}")
        # logger.info(f"Meta: {json.dumps(json_data, default=str)}")
        with open(fp, "w") as f:
            json.dump(json_data, f)
        logger.info(f"Metadata was saved to {str(fp)}")
    except Exception as e:
        logger.exception(
            f"Writing metadata in json to /efs directory failed. Error: {repr(e)}"
        )
        # _log_audit_event(
        #     key,
        #     AuditStatus.FAILED.value,
        #     "Error upon writing metadata.",
        # )
        raise


def _write_processed_ipynb_to_efs(ipynb: nbformat.NotebookNode, key: KeyPath) -> None:
    nbformat.write(ipynb, key.efs_filepath)


def _unmarshall_json(key: KeyPath) -> nbformat.NotebookNode:
    with open(key, "r") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)
    return nb


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
