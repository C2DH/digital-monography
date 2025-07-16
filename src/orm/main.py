import datetime
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import json
import os
import logging
import pathlib
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
import sqlmodel
import typing as t
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)

try:
    from constants import MediumEnum, IS_DEBUG
    from keys import KeyPath
    from models import Asset, File
    from lambda_wsgi import response as lambda_wsgi_response
except (ImportError, ModuleNotFoundError):
    from .constants import MediumEnum, IS_DEBUG  # type: ignore
    from .keys import KeyPath
    from .models import Asset, File
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
app.debug = IS_DEBUG
app.secret_key = os.environ["FLASK_SECRET_KEY"]
engine = sqlmodel.create_engine(os.environ["DB_URL"])
# engine = sa.create_engine(os.environ["DATABASE_URL"])
# session_factory = sa_orm.sessionmaker(bind=engine)


@app.route("/write", methods=["GET"])
def write() -> flask.Response:
    logger.info("write")
    slug = flask.request.args.get("slug")
    logger.info("slug: %s", slug)
    # assert slug is not None, "Error: slug was not provided"

    # path = pathlib.Path("/tmp/efs/a_book/01_a.md")
    # medium = MediumEnum.PAPER
    # location = KeyPath("/mnt/efs/a_book/01_a.md")

    with sqlmodel.Session(engine) as session:
        session.add(File(stem="stem", prefix="prefix"))
        session.add(
            Asset(
                fp=pathlib.PosixPath("foo/bar/1.txt"),
                metadata_table="0a7bf8c-0a7b-4b8c-0a7b-f8c0a7bf8c0a",
                medium=MediumEnum.PAPER,
                slug="slug",
                author="author",
                source="source",
                location=KeyPath("foo/bar/config.yml"),
                alttext="alttext",
                caption="caption",
                comments="comments",
                target="target",
                is_color=True,
                is_ready=False,
            )
        )
        session.commit()

        # stem=stem, prefix=str(prefix)

    resp = flask.Response(
        response=flask.json.dumps({"a": "1", "b": "2"}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/read", methods=["GET"])
def read() -> flask.Response:
    with sqlmodel.Session(engine) as session:
        stmt = sqlmodel.select(Asset)
        res = session.exec(stmt)
        for asset in res:
            print(asset)
        assets = res.all()
        print(assets)
        asset = res.first()
        print(asset)
        # File
        stmt = sqlmodel.select(File)
        res = session.exec(stmt)
        for asset in res:
            print(asset)
        assets = res.all()
        print(assets)
        asset = res.first()
        print(asset)
    resp = flask.Response(
        response=flask.json.dumps({"a": "1", "b": "2"}),
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


if __name__ == "__main__":
    app.run()
