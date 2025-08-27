import flask
import sqlmodel

from src._common.models import Asset

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from fetchers import select_by_slug
except (ImportError, ModuleNotFoundError):
    # in local testing, db and fetchers are one directory up
    from ..db import db_engine
    from ..fetchers import select_by_slug


assets_bp = flask.Blueprint("assets", __name__)


@assets_bp.route("/assets/list", methods=["GET"])
def assets_list() -> flask.Response:
    """
    List models.Asset objects by a "slug" parameter. See example URL:
    /assets/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = select_by_slug(session, Asset, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp
