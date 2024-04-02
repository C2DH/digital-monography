# import pathlib
import re
import time
import boto3
import json
import logging
import os
import typing as t
import urllib.parse

# import io
# from subprocess import Popen, PIPE, STDOUT

import bs4
import mammoth

try:
    from constants import DEFAULT_SFS_DIR
    from citations import add_citations_and_bibliography
    from md_extraction import BookMetadata
    from metadata_extraction import replace_assets_with_directives
    from html2md import convert_to_md

    # from keys import Key
except ModuleNotFoundError as e:
    from src.preparer.constants import DEFAULT_SFS_DIR
    from src.preparer.citations import add_citations_and_bibliography
    from src.preparer.md_extraction import BookMetadata
    from src.preparer.metadata_extraction import replace_assets_with_directives
    from src.preparer.html2md import convert_to_md

    # from src.preparer.keys import Key


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
    start = time.time()
    key = _get_key(event)
    # if not key.endswith(".docx"):
    #     logger.info(
    #         "Object {key} is not a `.docx` file. Closing the Preparer Lambda function."
    #     )
    #     return {"statusCode": 200, "body": ""}
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    html_str = _convert_to_html(key)
    html_soup = _get_html_soup(html_str)
    metadata = _get_book_metadata()
    html_soup = _add_citations_and_bibliography(html_soup)
    html_soup = _replace_assets_with_directives(html_soup, metadata)
    _put_html_to_s3(str(html_soup), key)

    # wc
    md = _convert_to_md(html_soup, metadata)
    words = re.findall("[a-zA-Z_]+", md)
    char_count = len("".join(words))
    word_count = len(words)
    end = time.time()
    delta_in_sec = end - start
    delta_in_ms = delta_in_sec * 1000  # milliseconds
    templ = """<!DOCTYPE html><html>
<head>
  <title>The title</title>
</head>
<body>
<div id="book-metadata-tbl">
<p>==========================================</p>
<table>
  <caption>
    Details about the current document (estimates)
  </caption>
  <tbody>
    <tr>
      <td>
        Word count:
      </td>
      <td>{word_count}</td>
    </tr>
    <tr>
      <td>
        Characted count:
      </td>
      <td>{char_count}</td>
    </tr>
    <tr>
      <td>
        Execution time (s):
      </td>
      <td>{delta_in_sec:.4f} seconds</td>
    </tr>
    <tr>
      <td>
        Execution time (ms):
      </td>
      <td>{delta_in_ms:.2f} milliseconds</td>
    </tr>
  </tbody>
</table>
<p>==========================================</p>
</div>
</body>
</html>
""".format(
        word_count=word_count,
        char_count=char_count,
        delta_in_sec=delta_in_sec,
        delta_in_ms=delta_in_ms,
    )
    new_html_soup = bs4.BeautifulSoup(templ, "html.parser")
    new_html_soup.html.body.append(html_soup)
    # html_soup.append(bs4.BeautifulSoup(templ, "html.parser"))
    _put_md_to_s3(str(new_html_soup), key)  # for presentation purposes show raw html
    THIS_WORKS_DISABLED_FOR_DEMO_PURPOSES = """
    md = _convert_to_md(html_soup, metadata)
    _put_md_to_s3(md, key)
    """
    return {"statusCode": 200, "body": ""}


def _get_key(event) -> str:
    try:
        key_str = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
        )
        logger.info(f"Key {key_str} was found in the event records.")
        # key = Key(key_str, is_upload=True)
        # logger.info(f"Key {str(key)} was created.")
        return key_str
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
        # logging.info("ls -la /tmp")
        # process = Popen("ls -la /tmp".split(), stdout=PIPE, stderr=STDOUT)
        # with process.stdout:
        #     for line in iter(process.stdout.readline, b""):
        #         logging.info(line)

        # os.mkdir(f"/tmp/{key.slug}", 0o777)
        # # os.system(f"chown -R 777 /tmp/{key.slug}")  # this won't work on Windows
        # key.mkdir()

        # logger.info(f"Do I have to explicitly stringify keys? {key}!")

        # p = pathlib.Path(f"/tmp/{key.slug}")
        # p.parent.mkdir(exist_ok=True, parents=True)

        # try:
        #     os.mkdir(f"/tmp/{key.slug}", mode=0x755)
        # except PermissionError:
        #     logging.info("Mode 0x755 did not work. Trying 0x777")
        #     os.mkdir(f"/tmp/{key.slug}", mode=0x777)

        # logging.info("ls -la /tmp")
        # process = Popen("ls -la /tmp".split(), stdout=PIPE, stderr=STDOUT)
        # with process.stdout:
        #     for line in iter(process.stdout.readline, b""):
        #         logging.info(line)

        # try:
        #     os.chmod(f"/tmp/{key.slug}", mode=0x777)
        # except PermissionError:
        #     logging.info('os.chmod(f"/tmp/key.slug", mode=0x777)')

        # logging.info("ls -la /tmp")
        # process = Popen("ls -la /tmp".split(), stdout=PIPE, stderr=STDOUT)
        # with process.stdout:
        #     for line in iter(process.stdout.readline, b""):
        #         logging.info(line)

        # logging.info(
        #     'os.path.isfile(f"/tmp/key")=' + str(os.path.isfile(f"/tmp/{key}"))
        # )
        # logging.info('os.path.isdir(f"/tmp/key")=' + str(os.path.isdir(f"/tmp/{key}")))

        with open(f"/{DEFAULT_SFS_DIR}/{str(key)}", "wb") as fileobj:
            resp = s3.download_fileobj(src, str(key), fileobj)
            logger.info(
                f"Response from s3.download_fileobj(Bucket={src}, Key={str(key)}): "
                + json.dumps(resp, default=str)
            )

            # fileobj = io.BytesIO
            # s3.download_fileobj(src, str(key), fileobj)
            # fileobj.seek(0)

    except Exception as e:
        logger.exception(
            f"Downloading fileobj {str(key)} from {src} failed. Error: {repr(e)}"
        )
        raise


def _convert_to_html(key: str) -> str:
    try:
        # logging.info("ls -la /tmp")
        # process = Popen("ls -la /tmp".split(), stdout=PIPE, stderr=STDOUT)
        # with process.stdout:
        #     for line in iter(process.stdout.readline, b""):
        #         logging.info(line)
        with open(f"/{DEFAULT_SFS_DIR}/{key}", "rb") as f:
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


def _put_html_to_s3(contents: str, key: str) -> None:
    try:
        _put_object(
            contents.encode("utf-8"),
            IR_APKG_HTML_BUCKET_NAME,
            key.replace(".docx", ".html"),
        )
    except Exception as e:
        logger.exception(f"Putting html to s3 bucket failed. Error: {repr(e)}")
        raise


def _put_md_to_s3(contents: str, key: str) -> None:
    try:
        _put_object(
            contents.encode("utf-8"),
            IR_APKG_MD_BUCKET_NAME,
            key.replace(".docx", ".html"),
            # md.encode("utf-8"), IR_APKG_MD_BUCKET_NAME, key.replace(".docx", ".md")
        )
    except Exception as e:
        logger.exception(f"Putting md to s3 bucket failed. Error: {repr(e)}")
        raise
