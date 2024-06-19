import bs4
import boto3
import datetime
import logging
import pathlib
import typing as t
import urllib.parse

try:
    from constants import (
        # ARCHIVE_APKG_ALL,
        # IR_APKG_HTML_BUCKET_NAME,
        # IR_APKG_MD_BUCKET_NAME,
        IS_DEBUG,
    )
    from fakers import Faker
    from keys import KeyPath

except ModuleNotFoundError as e:
    from src.preparer.constants import (
        # ARCHIVE_APKG_ALL,
        # IR_APKG_HTML_BUCKET_NAME,
        # IR_APKG_MD_BUCKET_NAME,
        IS_DEBUG,
    )
    from src.preparer.fakers import Faker
    from src.preparer.keys import KeyPath


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}.log")
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
    s3 = Faker("s3")
else:
    s3 = boto3.client("s3")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    key = _get_key(event)
    if key.suffix.lower() == ".md":
        return {"statusCode": 200, "body": ""}
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


def _get_html_soup(html: str) -> bs4.BeautifulSoup:
    try:
        return bs4.BeautifulSoup(html, "html.parser")
    except Exception as e:
        logger.exception(f"Creation of bs4.BeautifulSoup failed. Error: {repr(e)}")
        raise
