import datetime
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import json
import os
import logging
import pathlib
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)

try:
    from constants import IS_DEBUG
    from lambda_wsgi import response as lambda_wsgi_response
except (ImportError, ModuleNotFoundError):
    from .constants import IS_DEBUG  # type: ignore
    from .lambda_wsgi import response as lambda_wsgi_response  # type: ignore


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


app = flask.Flask(__name__)
app.debug = True
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context: LambdaContext):
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Context: {json.dumps(context, default=str)}")
    return lambda_wsgi_response(app, event, context)
