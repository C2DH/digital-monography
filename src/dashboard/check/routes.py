import flask

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


check_bp = flask.Blueprint("check", __name__)


@check_bp.route("/b/<slug>/check/", methods=["GET"])
def index() -> flask.Response:
    return (
        flask.jsonify({"todo": "display check results"}),
        200,
    )
