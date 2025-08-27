import flask
import logging
import sqlmodel

from src._common.models import Heading
from ..db import db_engine
from ..fetchers import select_by_slug


headings_bp = flask.Blueprint("headings", __name__)


@headings_bp.route("/headings/list", methods=["GET"])
def headings_list() -> flask.Response:
    """
    List models.Heading object by a "slug" parameter. See example URL:
    /headings/list?slug=a_book
    """
    logging.info("/headings/list")
    slug = flask.request.args.get("slug")
    logging.info(f"route: /headings/list slug: {slug}")
    with sqlmodel.Session(db_engine) as session:
        db_data = select_by_slug(session, Heading, slug)
    resp = flask.Response(
        response=flask.json.dumps(db_data, default=str),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp
