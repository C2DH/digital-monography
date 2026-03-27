import flask

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


info_bp = flask.Blueprint("info", __name__)


@info_bp.route("/b/<slug>/info/", methods=["GET"])
def index() -> flask.Response:
    return (
        flask.jsonify({"todo": "display book info"}),
        200,
    )
