import base64
import bs4
import boto3
import json
import logging
import mammoth
import re
import requests
import time
import typing as t
import urllib.parse

try:
    from constants import (
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        GITHUB_ORG,
        GITHUB_TOKEN,  # TODO: fetch from AWS Secrets Manager
    )
    from citations import add_citations_and_bibliography
    from md_extraction import BookMetadata
    from metadata_extraction import replace_assets_with_directives
    from html2md import convert_to_md
    from keys import KeyPath
except ModuleNotFoundError as e:
    from src.preparer.constants import (
        IR_APKG_HTML_BUCKET_NAME,
        IR_APKG_MD_BUCKET_NAME,
        GITHUB_ORG,
        GITHUB_TOKEN,  # TODO: fetch from AWS Secrets Manager
    )
    from src.preparer.citations import add_citations_and_bibliography
    from src.preparer.md_extraction import BookMetadata
    from src.preparer.metadata_extraction import replace_assets_with_directives
    from src.preparer.html2md import convert_to_md
    from src.preparer.keys import KeyPath


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3 = boto3.client("s3")
# secretsmanager = boto3.client("secretsmanager")
# resp = secretsmanager.get_secret_value(SecretId="dgtmon-dev-github-api-token")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Starting Dockerized Lambda.")
    start = time.time()
    key = _get_key(event)
    src = _get_source_bucket(event)
    _download_fileobj(src, key)
    _create_github_repo(key)
    if not key.suffix.lower() == ".docx":
        r = _get_from_github_repo(key)
        prev_v_sha = r.json().get("sha", None)
        _put_to_github_repo(key, prev_v_sha, event, context)
        return {"statusCode": 200, "body": ""}
    html_str = _convert_to_html(key)
    html_soup = _get_html_soup(html_str)
    metadata = _get_book_metadata()
    html_soup = _add_citations_and_bibliography(html_soup)
    html_soup = _replace_assets_with_directives(html_soup, metadata)
    _put_html_to_s3(str(html_soup), key)
    md = _convert_to_md(html_soup, metadata)
    _write_processed_md_to_efs(md, key)
    # _put_md_to_s3(md, key) # TODO: This is disabled only for testing
    r = _get_from_github_repo(key)
    prev_v_sha = r.json().get("sha", None)
    _put_to_github_repo(key.efs_filepath.with_suffix(".md"), prev_v_sha, event, context)
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


def _write_processed_md_to_efs(md: str, key: KeyPath):
    new_efs_filepath = key.efs_filepath.with_suffix(".md")
    with open(new_efs_filepath, "w") as f:
        f.write(md)


def _create_github_repo(key: KeyPath) -> requests.Response:
    """
    Creates a new repository in the specified organization.
    Note that the GitHub API token must have the write "Administration" repo permissions.
    If the repository already exists, the repository creation will fail with a message
    "name already exists on this account".
    See API docs here:
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-an-organization-repository
    """
    data = {
        "name": key.slug,
        # "description": "",  # TODO: get a desc from `key.efs_slug_dir / "_config.yml"`
        # "homepage": "",  # TODO: link to the digital version of the book
        "private": False,
        "visibility": "public",
        "security_and_analysis": None,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
        "is_template": False,
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        res = requests.post(
            f"https://api.github.com/orgs/{GITHUB_ORG}/repos",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json()), default=str)
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        raise


def _get_from_github_repo(key: KeyPath) -> requests.Response:
    """
    Gets the contents of a file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
    """
    try:
        res = requests.get(
            f"https://api.github.com/repos/{GITHUB_ORG}/{key.slug}/contents/{key.github_path}",
        )
        logger.info(json.dumps(res.json()), default=str)
        return res
    except Exception as e:
        logger.error(
            f"Unable to retrieve the previous version of the {key.s3_key} file. Error: {repr(e)}"
        )
        raise


def _put_to_github_repo(
    key: KeyPath, prev_v_sha: t.Optional[str], event, context
) -> requests.Response:
    """
    Creates a new file or replaces an existing file in a repository.
    See API docs here:
    https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents
    """
    with open(key.efs_filepath, "rb") as fileobj:
        b64content = base64.b64encode(fileobj.read()).decode()
    try:
        logger.info("s3 event: " + json.dumps(event, default=str))
        logger.info("s3 context: " + json.dumps(context, default=str))
        eventSource = event["Records"][0]["eventSource"]
        eventName = event["Records"][0]["eventName"]
        eventTime = event["Records"][0]["eventTime"]
        requestId = event["Records"][0]["responseElements"]["x-amz-request-id"]
    except Exception as e:
        logger.error(f"Unable to retrieve the event data. Error: {repr(e)}")
        raise
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "message": f"{eventSource}:{eventName} to {key.s3_key} on {eventTime} id {requestId}",  # TODO: improve commit message
        "content": b64content,
        # "committer": { # TODO: figure out how to extract data of the commiter & author
        #     "name": "",
        #     "email": "",
        # },
        # "author": {
        #     "name": "",
        #     "email": "",
        # },
    }
    if prev_v_sha:
        data.update({"sha": prev_v_sha})
    try:
        res = requests.put(
            f"https://api.github.com/repos/{GITHUB_ORG}/{key.slug}/contents/{key.github_path}",
            json=data,
            headers=headers,
        )
        logger.info(json.dumps(res.json()), default=str)
        return res
    except Exception as e:
        logging.exception(
            f"Error while sending request to update github repo: {repr(e)}"
        )
        raise


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
