import base64
import datetime
import json
import pathlib
import logging

try:
    from constants import (
        IS_DEBUG,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        IS_DEBUG,
    )


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


def lambda_handler(event, context):
    logger.info("Event" + json.dumps(event, default=str))
    logger.info("Context" + json.dumps(context, default=str))

    msg = base64.b64decode(event["Records"][0]["body"])
    logger.info(f"Message: {msg}")
    return
