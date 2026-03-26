import flask


home_bp = flask.Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def index() -> flask.Response:
    return flask.render_template("home/index.html")
