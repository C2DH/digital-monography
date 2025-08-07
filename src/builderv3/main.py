import subprocess
import boto3
import datetime
import logging
import json
import pathlib
import typing as t
from mypy_boto3_dynamodb.service_resource import (
    DynamoDBServiceResource as boto3_DynamoDBServiceResource,
)

# I cannot just install and import jupyter-book v2, because it would cause
# conflicts with jupyter-book v1, which is used in builder. I wouldn't be able to
# run both versions in the same environment.


try:
    from audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from constants import (
        IS_DEBUG,
        ModuleEnum,
    )
    from keys import KeyPath
except (ImportError, ModuleNotFoundError):
    from .audit import AuditEvent, AuditStatus, AlertLog, AlertStatus
    from .constants import (
        IS_DEBUG,
        ModuleEnum,
    )
    from .keys import KeyPath


if IS_DEBUG:
    today = datetime.date.today().isoformat()
    log_target = pathlib.Path(f"/tmp/efs/_LOGS/{today}_builderv2.log")
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
else:
    dynamodb: boto3_DynamoDBServiceResource = boto3.resource("dynamodb")


def lambda_handler(event, context) -> dict[str, t.Union[str, int]]:
    logger.info("Event: " + json.dumps(event, default=str))
    logger.info("Context: " + json.dumps(context, default=str))
    key = KeyPath("/tmp/efs/aslug/test.txt")
    _build_jb2_book(key)


def _build_jb2_book(key: KeyPath) -> None:
    try:
        result = subprocess.run(["myst", "build", "--html", "--ci"])
        print("result", result)
    except Exception as e:
        msg = f"Unable to build JBv2 book. Error: {repr(e)}"
        logging.exception(msg)
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while Jupyter Book v2 build operation.",
        )
        raise


def _distribute_jb2_book(key: KeyPath) -> None:
    try:
        pass
        # probably just send sqs message with new status to github microservice to:

        # 1. call github api to create Github Pages site
        # https://docs.github.com/en/rest/pages/pages?apiVersion=2022-11-28#create-a-github-pages-site

        # 2. (maybe) call github api to update information about the site
        # https://docs.github.com/en/rest/pages/pages?apiVersion=2022-11-28#update-information-about-a-github-pages-site
    except Exception as e:
        msg = f"Failed to distribute JBv2 book build. Error: {repr(e)}"
        logging.exception(msg)
        _log_audit_event(
            key,
            AuditStatus.FAILED.value,
            "Error while updating the digital version (JBv2).",
        )
        raise


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
