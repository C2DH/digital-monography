import flask


info_bp = flask.Blueprint("info", __name__)


@info_bp.route("/b/<slug>/info/", methods=["GET"])
def index() -> flask.Response:
    return (
        flask.jsonify({"todo": "display book info"}),
        200,
    )
