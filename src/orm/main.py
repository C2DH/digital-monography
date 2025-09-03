import datetime
import logging
import json
import os
import pathlib
import sys
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)
import flask

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.constants import IS_DEBUG
from src._common.models import *
from lambda_wsgi import response as lambda_wsgi_response
from app import create_app


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


app = create_app()


@app.route("/", methods=["GET"])
def index() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "home", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/api", methods=["GET"])
@app.route("/api/", methods=["GET"])
def index() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "home", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/hello", methods=["GET"])
@app.route("/hello/", methods=["GET"])
def index() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "home", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/api/hello", methods=["GET"])
@app.route("/api/hello/", methods=["GET"])
def index() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "home", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context: LambdaContext):
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Context: {json.dumps(context, default=str)}")
    return lambda_wsgi_response(app, event, context)


# print(app.url_map)
