import alembic
import alembic.config
import datetime
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import json
import os
import logging
import pathlib
import sqlmodel
import sqlmodel.main
import sys
import typing as t
import uuid
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)

# Get the current directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src._common.constants import DEFAULT_SFS_DIR, DB_URL, IS_DEBUG
from src._common.models import *
from lambda_wsgi import response as lambda_wsgi_response


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


@app.route("/admin/migrate", methods=["GET"])
def admin_migrate() -> flask.Response:
    """
    Migrate the database schema.
    """
    msg = {"status": "success", "message": "ok"}
    status = 200
    try:
        alembicArgs = [
            "-c",
            os.path.join("src", "_common", "alembic.ini"),
            # "--sqlalchemy-url",
            # DB_URL,
            "--raiseerr",
            "upgrade",
            "head",
        ]
        alembic.config.main(argv=alembicArgs)
    except Exception as e:
        status = 503
        logger.error(f"Error migrating database: {e}")
        msg = {"status": "error", "message": str(e)}
    resp = flask.Response(
        response=flask.json.dumps(msg, default=str),
        status=status,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/admin/unlink", methods=["GET"])
def unlink() -> flask.Response:
    """
    Delete the database. This is mean only for debugging.
    TODO: Disable when the db schema stabilizes.
    """
    msg = {"status": "success", "message": "ok"}
    status = 200
    try:
        db_path = os.environ.get("DB_PATH")
        if db_path:
            db = pathlib.Path(db_path)
        else:
            db = pathlib.Path(DEFAULT_SFS_DIR) / "_database.db"
        db.unlink(missing_ok=True)
    except Exception as e:
        status = 503
        logger.error(f"Error deleting the database: {e}")
        msg = {"status": "error", "message": str(e)}
    resp = flask.Response(
        response=flask.json.dumps(msg, default=str),
        status=status,
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

    if not slug:
        resp = flask.Response(
            response=flask.json.dumps(
                {"status": "error", "message": "slug parameter is required"}
            ),
            status=400,
            mimetype="application/json",
        )
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
        return resp
    with sqlmodel.Session(db_engine) as session:
        session.add(
            Asset(
                **{
                    "metadata_table": "1a019cdf-d0f1-47e0-b954-ecd2e2aaae33",
                    "slug": slug,
                    "author": "",
                    "source": "",
                    "alttext": "",
                    "caption": "",
                    "orig_caption": "",
                    "comments": "Looks good",
                    "target": "",
                    "is_color": None,
                    "is_ready": True,
                    "is_on_paper": False,
                    "rest": '{"deleteprevious": true}',
                    "height": None,
                    "pk": uuid.uuid4().hex,
                    "loc": "book-content-examples/metadata_extraction.docx",
                    "fp": "assets/10x10px-img.png",
                    "medium": "D",
                    "location": "book-content-examples/metadata_extraction.docx",
                }
            )
        )
        session.commit()
    resp = flask.Response(
        response=flask.json.dumps({"status": "success", "message": "ok"}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/read", methods=["GET"])
def read() -> flask.Response:
    logger.info("read")
    slug = flask.request.args.get("slug")
    logger.info("slug: %s", slug)
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.select(Asset).where(Asset.slug == slug)
        res = session.exec(stmt).all()
        assets = [ass.model_dump(mode="json") for ass in res]
    resp = flask.Response(
        response=flask.json.dumps(assets),
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
