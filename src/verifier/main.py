import datetime
import boto3
import logging
import os
import pathlib
import typing as t


IS_DEBUG = bool(int(os.environ.get("DGTMON_DEBUG", 0)))
if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_verifier.log")
    log_target.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_target,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s::%(name)s::%(levelname)s::%(message)s",
    )
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    from fakers import Faker
except ModuleNotFoundError as e:
    from src.verifier.fakers import Faker


if IS_DEBUG:
    s3 = Faker("s3")
    sqs = Faker("sqs")
else:
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Handler was invoked successfully.")
    logger.info("s3: " + str(type(s3)))
    logger.info("sqs: " + str(type(sqs)))
    return {"statusCode": 200, "body": ""}


def _fromtimestamp(event_time: str) -> datetime.datetime:
    return datetime.datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S.%f%z")
