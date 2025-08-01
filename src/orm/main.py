import datetime
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import json
import os
import logging
import pathlib
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
import sqlmodel
import sqlmodel.main
import typing as t
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)

try:
    from constants import MediumEnum, DB_URL, IS_DEBUG
    from keys import KeyPath
    from lambda_wsgi import response as lambda_wsgi_response
    from models import Asset, CitationGroup, CitationItem, Heading
except (ImportError, ModuleNotFoundError):
    from .constants import MediumEnum, DB_URL, IS_DEBUG  # type: ignore
    from .keys import KeyPath  # type: ignore
    from .lambda_wsgi import response as lambda_wsgi_response  # type: ignore
    from .models import Asset, CitationGroup, CitationItem, Heading  # type: ignore


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
db_engine = sqlmodel.create_engine(DB_URL)


@app.route("/", methods=["GET"])
def index() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "index", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


def _select_by_slug(
    session: sqlmodel.Session,
    model: Asset | CitationGroup | CitationItem | Heading,
    slug: str,
) -> list[dict[str, str | int | bool]]:
    """
    Query the database for a model by its slug and dump to a json serializable format.
    """
    assert isinstance(model, sqlmodel.main.SQLModelMetaclass)
    if not hasattr(model, "slug"):
        logger.error(f"Model {model.__name__} does not have a 'slug' attribute.")
        return []
    res = []
    statement = sqlmodel.select(model).where(model.slug == slug)
    query_result = session.exec(statement)
    for dp in query_result:
        dp: sqlmodel.SQLModel
        res.append(dp.model_dump(mode="json"))
    return res


@app.route("/assets/list", methods=["GET"])
def assets_list() -> flask.Response:
    """
    List models.Asset objects by a "slug" parameter. See example URL:
    /assets/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = _select_by_slug(session, Asset, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/headings/list", methods=["GET"])
def headings_list() -> flask.Response:
    """
    List models.Heading object by a "slug" parameter. See example URL:
    /headings/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = _select_by_slug(session, Heading, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/citations/groups/list", methods=["GET"])
def citations_groups_list() -> flask.Response:
    """
    List objects.CitationGroup object by a "slug" parameter. See example URL:
    /citations/groups/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = _select_by_slug(session, CitationGroup, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/citations/items/list", methods=["GET"])
def citations_items_list() -> flask.Response:
    """
    List objects.CitationItems object by a "slug" parameter. See example URL:
    /citations/items/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = _select_by_slug(session, CitationItem, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/write", methods=["GET"])
def write() -> flask.Response:
    logger.info("write")
    slug = flask.request.args.get("slug")
    logger.info("slug: %s", slug)
    # assert slug is not None, "Error: slug was not provided"

    # path = pathlib.Path("/tmp/efs/a_book/01_a.md")
    # medium = MediumEnum.PAPER
    # location = KeyPath("/mnt/efs/a_book/01_a.md")

    with sqlmodel.Session(db_engine) as session:
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
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.select(Asset)
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
    app.run(port=8001)
