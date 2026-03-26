import flask


check_bp = flask.Blueprint("check", __name__)


@check_bp.route("/b/<slug>/check/", methods=["GET"])
def index() -> flask.Response:
    return (
        flask.jsonify({"todo": "display check results"}),
        200,
    )
