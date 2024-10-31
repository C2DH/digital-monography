import datetime
import pathlib
import bs4
import boto3
import json
import logging
import mammoth
import nbformat
import typing as t
import urllib.parse

# import yaml

try:
    from constants import (
        ARCHIVE_APKG_ALL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        IS_DEBUG,
    )
    from citations import add_bibliography, is_citation, prepare_citations
    from hide_metadata_in_html import hide_metadata_in_html
    from metadata import DocumentMetadata
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
    from html2md import convert_to_md
    from ipynb_prep import tags_to_myst_crossref_targets
    from keys import KeyPath
    from fakers import Faker
except (ImportError, ModuleNotFoundError):
    from .constants import (
        ARCHIVE_APKG_ALL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        IS_DEBUG,
    )
    from .citations import add_bibliography, is_citation, prepare_citations
    from .hide_metadata_in_html import hide_metadata_in_html
    from .metadata import DocumentMetadata
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
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")


def is_table(tag: bs4.element.Tag) -> bool:
    return bool(tag.name == "table")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    images_with_alttxt = []
    tables = []
    headers = []
    captions = []
    citations = []
    footnotes = []
    references = []
    key = _get_key(event)
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    if key.suffix.lower() == ".ipynb":
        ipynb: nbformat.NotebookNode = _unmarshall_json(key.efs_filepath)
        tags_to_myst_crossref_targets(ipynb)
        _write_processed_ipynb_to_efs(ipynb, key)
        ARCHIVE = "_put_to_archive_s3(key)"
        return {"statusCode": 200, "body": ""}
    if key.suffix.lower() == ".docx":
        html_str = _convert_to_html(key.efs_filepath)
        metadata = DocumentMetadata(key)
        html_soup = bs4.BeautifulSoup(html_str, "html.parser")
        classifiers = [
            (is_img_with_alt_text, images_with_alttxt),
            (is_citation, citations),
            (is_table, tables),
            (is_header, headers),
            (is_caption, captions),
            (is_footnote, footnotes),
            (is_reference, references),
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
        html_soup = prepare_metadata_tables(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_headers(html_soup, metadata, headers)
        html_soup = prepare_ref_targets_in_captions(html_soup, metadata, captions)
        html_soup = prepare_ref_targets_in_footnotes(html_soup, metadata, footnotes)
        html_soup = prepare_references(html_soup, metadata, references)
        html_soup = remove_empty_tables(html_soup, metadata, tables)
        html_soup = prepare_alt_texts(html_soup, metadata, images_with_alttxt)
        html_soup = hide_metadata_in_html(html_soup, metadata)  # last step
        html_soup_str = str(html_soup)
        # IMPORTANT NOTE: other services depend on html produced at this stage, make sure that:
        # 1) all reversible transformations are made before saving html file;
        # 2) irreversible transformations are omited to avoid not being able to recreate a book
        # as html files written at this stage will be the basis for a paper version of a book.
        _write_config_to_efs(metadata, key)
        _write_processed_html_to_efs(html_soup_str, key)
        _put_html_to_s3(html_soup_str, key)
        md = _convert_to_md(html_soup, metadata)
        _write_processed_md_to_efs(md, key)
        _put_md_to_s3(md, key)
        ARCHIVE = '_put_to_archive_s3(key.s3_key.with_suffix(".md"), md)'
        return {"statusCode": 200, "body": ""}
    else:
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
        key.parent.mkdir(parents=True, exist_ok=True)
        with open(key, "wb") as fileobj:
            s3_key = str(key.s3_key)
            resp = s3.download_fileobj(src, s3_key, fileobj)
            logger.info(
                f"Response from s3.download_fileobj(Bucket={src}, Key={s3_key}): "
                + json.dumps(resp, default=str)
            )
    except Exception as e:
        logger.exception(
            f"Downloading fileobj {str(key)} from {src} failed. Error: {repr(e)}"
        )
        raise


def _convert_to_html(key: KeyPath) -> str:
    try:
        with open(key, "rb") as f:
            style_mappings = """
            p[style-name='Quote'] => blockquote:fresh
            p[style-name='Caption'] => p.dgt-mon-caption:fresh
            """
            result = mammoth.convert_to_html(f, style_map=style_mappings)
            logger.info(f"Converting {key} to html succedded.")
            return result.value
    except Exception as e:
        logger.exception(f"Converting {key} to html failed. Error: {repr(e)}")
        raise


def _convert_to_md(html_soup: bs4.BeautifulSoup, metadata: DocumentMetadata) -> str:
    try:
        return convert_to_md(html_soup, metadata)
    except Exception as e:
        logger.exception(f"Converting to md failed. Error: {repr(e)}")
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
        raise


def _put_html_to_s3(contents: str, key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".html")
        _put_object(
            contents.encode("utf-8"),
            IR_APKG_HTML_BUCKET_NAME,
            s3_key,
        )
    except Exception as e:
        logger.exception(f"Putting html to s3 bucket failed. Error: {repr(e)}")
        raise


def _put_md_to_s3(contents: str, key: KeyPath) -> None:
    try:
        s3_key = key.s3_key.with_suffix(".md")
        _put_object(
            contents.encode("utf-8"),
            IR_APKG_MD_BUCKET_NAME,
            s3_key,
        )
    except Exception as e:
        logger.exception(f"Putting md to s3 bucket failed. Error: {repr(e)}")
        raise


def _put_to_archive_s3(key: KeyPath, contents: t.Optional[str] = None) -> None:
    try:
        if contents is None:
            try:
                with open(key.efs_filepath, "r") as f:
                    contents = f.read()
            except UnicodeDecodeError as e:
                with open(key.efs_filepath, "rb") as f:
                    contents = f.read().decode("utf-8", "ignore")

        _put_object(
            contents.encode("utf-8"),
            ARCHIVE_APKG_ALL,
            key.s3_key,
        )
    except Exception as e:
        logger.exception(f"Putting file to archive s3 bucket failed. Error: {repr(e)}")
        raise


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


def _write_processed_ipynb_to_efs(ipynb: nbformat.NotebookNode, key: KeyPath) -> None:
    nbformat.write(ipynb, key.efs_filepath)


def _unmarshall_json(key: KeyPath) -> nbformat.NotebookNode:
    with open(key, "r") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)
    return nb
