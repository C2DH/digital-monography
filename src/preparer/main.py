import boto3
import json
import logging
import os
import typing as t
import urllib.parse

import bs4
import mammoth

try:
    from citations import add_citations_and_bibliography
    from md_extraction import BookMetadata
    from metadata_extraction import replace_assets_with_directives
    from html2md import convert_to_md
except ModuleNotFoundError:
    from src.preparer.citations import add_citations_and_bibliography
    from src.preparer.md_extraction import BookMetadata
    from src.preparer.metadata_extraction import replace_assets_with_directives
    from src.preparer.html2md import convert_to_md


try:
    IS_LOCAL = os.environ["PWD"].endswith("dhj-local")
except KeyError:
    IS_LOCAL = False
# DESTINATION_BUCKET = "dgtmon-dev-ir-apkg-md"
IR_APKG_HTML_BUCKET_NAME = "dgtmon-dev-ir-apkg-html"
IR_APKG_MD_BUCKET_NAME = "dgtmon-dev-ir-apkg-md"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_aws_client(service: str) -> t.Any:
    if IS_LOCAL:
        return boto3.client(
            service,
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="eu-central-1",
            endpoint_url="http://localhost:4566",
        )  # type: ignore
    else:
        return boto3.client(service)  # type: ignore


s3 = get_aws_client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Preparer Lambda function was successfully invoked.")
    key = _get_key(event)
    if not key.endswith(".docx"):
        logger.info(
            "Object {key} is not a `.docx` file. Closing the Preparer Lambda function."
        )
        return {"statusCode": 200, "body": ""}
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    html_str = _convert_to_html(key)
    html_soup = _get_html_soup(html_str)
    metadata = _get_book_metadata()
    html_soup = _add_citations_and_bibliography(html_soup)
    html_soup = _replace_assets_with_directives(html_soup, metadata)
    md = _convert_to_md(html_soup, metadata)
    _put_html_to_s3(html_soup, key)
    _put_md_to_s3(md, key)
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> str:
    try:
        key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        logger.info(f"Key {key} was found in the event records.")
        return key
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


def _download_fileobj(src: str, key: str):
    try:
        with open(f"/tmp/{key}", "wb") as fileobj:
            resp = s3.download_fileobj(src, key, fileobj)
            logger.info(
                f"Response from s3.download_fileobj(Bucket={src}, Key={key}): "
                + json.dumps(resp, default=str)
            )
    except Exception as e:
        logger.exception(
            f"Downloading fileobj {key} from {src} failed. Error: {repr(e)}"
        )
        raise


def _convert_to_html(key: str) -> str:
    try:
        with open(f"/tmp/{key}", "rb") as f:
            style_mappings = """
            p[style-name='Quote'] => blockquote:fresh
            """
            result = mammoth.convert_to_html(f, style_map=style_mappings)
            logger.info(f"Result.value: {result.value}")
            return result.value
    except Exception as e:
        logger.exception(f"Converting {key} to html failed. Error: {repr(e)}")
        raise


def _get_html_soup(html: str) -> bs4.BeautifulSoup:
    try:
        # html_soup = bs4.BeautifulSoup(result.value, "html.parser")
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


def _put_object(body: bytes, dst: str, key: str) -> t.Any:
    try:
        resp = s3.put_object(Body=body.decode("utf-8"), Bucket=dst, Key=key)
        logger.info(
            f"Response from s3.put_object(Bucket={dst}, Key={key}): "
            + json.dumps(resp, default=str)
        )
        return resp
    except Exception as e:
        logger.exception(f"Put object {key} to bucket {dst} failed. Error: {repr(e)}")
        raise


def _put_html_to_s3(html_soup: str, key: str) -> None:
    try:
        _put_object(
            str(html_soup).encode("utf-8"),
            IR_APKG_HTML_BUCKET_NAME,
            key.replace(".docx", ".html"),
        )
    except Exception as e:
        logger.exception(f"Putting html to s3 bucket failed. Error: {repr(e)}")
        raise


def _put_md_to_s3(md: str, key: str) -> None:
    try:
        _put_object(
            md.encode("utf-8"), IR_APKG_MD_BUCKET_NAME, key.replace(".docx", ".md")
        )
    except Exception as e:
        logger.exception(f"Putting md to s3 bucket failed. Error: {repr(e)}")
        raise
