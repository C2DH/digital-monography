import flask
import flask_login
import sqlmodel

from src._common.constants import DEFAULT_SFS_DIR, INPUT_DIR, JB_DIR
from src._common.models import Book
from src._common.keys import KeyPath

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


build_bp = flask.Blueprint("build", __name__)


@build_bp.route("/b/<slug>/build", methods=["GET"])
def build_book(slug: str) -> flask.Response:
    """
    Build a Jupyter Book as a static site.
    """
    return flask.render_template("build/index.html")
