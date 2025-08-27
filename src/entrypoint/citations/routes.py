import flask
import sqlmodel

from src._common.models import CitationGroup, CitationItem
from ..db import db_engine
from ..selectors import select_by_slug


citations_bp = flask.Blueprint("citations", __name__)


@citations_bp.route("/citations/groups/list", methods=["GET"])
def citations_groups_list() -> flask.Response:
    """
    List objects.CitationGroup object by a "slug" parameter. See example URL:
    /citations/groups/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = select_by_slug(session, CitationGroup, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@citations_bp.route("/citations/items/list", methods=["GET"])
def citations_items_list() -> flask.Response:
    """
    List objects.CitationItems object by a "slug" parameter. See example URL:
    /citations/items/list?slug=a_book
    """
    slug = flask.request.args.get("slug")
    with sqlmodel.Session(db_engine) as session:
        db_data = select_by_slug(session, CitationItem, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp
