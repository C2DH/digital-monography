import aws_lambda_wsgi
import datetime
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import logging
import pathlib

try:
    from constants import (
        IS_DEBUG,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        IS_DEBUG,
    )


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
app.debug = True
app.secret_key = "FLASK_SECRET_KEY"


@app.route("/")
def index():
    logger.info("Index REST api endpoint was called.")
    return flask.render_template("index.html")


@app.route("/version")
def version():
    logger.info("Version REST api endpoint was called.")
    return {"version": "0.0.1"}


@app.route("/done")
def done():
    logger.info("Done REST api endpoint was called.")
    return flask.render_template("done.html")


def lambda_handler(event, context):
    logger.info("Lambda handler was called.")
    return aws_lambda_wsgi.response(app, event, context)
