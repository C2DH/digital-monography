import bs4
import boto3
import json
import logging
import mammoth
import re
import time
import typing as t
import urllib.parse

try:
    from constants import (
        ARCHIVE_APKG_ALL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
    )
    from citations import add_citations_and_bibliography
    from md_extraction import BookMetadata
    from metadata_extraction import replace_assets_with_directives
    from html2md import convert_to_md
    from keys import KeyPath
except ModuleNotFoundError as e:
    from src.preparer.constants import (
        ARCHIVE_APKG_ALL,
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
    )
    from src.preparer.citations import add_citations_and_bibliography
    from src.preparer.md_extraction import BookMetadata
    from src.preparer.metadata_extraction import replace_assets_with_directives
    from src.preparer.html2md import convert_to_md
    from src.preparer.keys import KeyPath


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    start = time.time()
    key = _get_key(event)
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    if not key.suffix.lower() == ".docx":
        _put_to_archive_s3(key)
        return {"statusCode": 200, "body": ""}
    html_str = _convert_to_html(key)
    html_soup = _get_html_soup(html_str)
    metadata = _get_book_metadata()
    html_soup = _add_citations_and_bibliography(html_soup)
    html_soup = _replace_assets_with_directives(html_soup, metadata)
    _put_html_to_s3(str(html_soup), key)
    md = _convert_to_md(html_soup, metadata)
    _write_processed_md_to_efs(md, key)
    _put_md_to_s3(md, key)
    _put_to_archive_s3(key.s3_key.with_suffix(".md"), md)
    _log_document_stats(start, md)
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


def _download_fileobj(src: str, key: KeyPath):
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
        key = key.efs_filepath
        with open(key, "rb") as f:
            style_mappings = """
            p[style-name='Quote'] => blockquote:fresh
            """
            result = mammoth.convert_to_html(f, style_map=style_mappings)
            logger.info(f"Converting {key} to html succedded.")
            return result.value
    except Exception as e:
        logger.exception(f"Converting {key} to html failed. Error: {repr(e)}")
        raise


def _get_html_soup(html: str) -> bs4.BeautifulSoup:
    try:
        return bs4.BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.exception(f"Creation of bs4.BeautifulSoup failed. Error: {repr(e)}")
        raise


def _get_book_metadata():
    try:
        return BookMetadata()
    except Exception as e:
        logger.exception(f"Creation of BookMetadata object failed. Error: {repr(e)}")
        raise


def _add_citations_and_bibliography(html_soup: bs4.BeautifulSoup):
    try:
        return add_citations_and_bibliography(html_soup)
    except Exception as e:
        logger.exception(
            f"Adding citations and bibliographies failed. Error: {repr(e)}"
        )
        raise


def _replace_assets_with_directives(
    html_soup: bs4.BeautifulSoup, metadata: BookMetadata
):
    try:
        return replace_assets_with_directives(html_soup, metadata)
    except Exception as e:
        logger.exception(f"Replacing assets with directives failed. Error: {repr(e)}")
        raise


def _convert_to_md(html_soup: bs4.BeautifulSoup, metadata: BookMetadata):
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
            with open(key.efs_filepath, "r") as f:
                contents = f.read()
            logger.info(f"Contents: " + contents)

        _put_object(
            contents.encode("utf-8"),
            ARCHIVE_APKG_ALL,
            key.s3_key,
        )
    except Exception as e:
        logger.exception(f"Putting file to archive s3 bucket failed. Error: {repr(e)}")
        raise


def _write_processed_md_to_efs(md: str, key: KeyPath):
    new_efs_filepath = key.efs_filepath.with_suffix(".md")
    with open(new_efs_filepath, "w") as f:
        f.write(md)


def _log_document_stats(start: float, md: str):
    words = re.findall("[a-zA-Z_]+", md)
    end = time.time()
    stats = {
        "char_count": len("".join(words)),
        "word_count": len(words),
        "delta_in_sec": end - start,
        "delta_in_ms": (end - start) * 1000,
    }
    logging.info(json.dumps(stats, default=str))
