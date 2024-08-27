import aws_lambda_wsgi
import boto3
import datetime
import dropbox
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import hashlib
import hmac
import json
import logging
import markdown
import os
import pathlib
import typing as t
import urllib

try:
    from constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
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


secretsmanager = boto3.client("secretsmanager")


APP_KEY = "9d9sdu2khx0lboj"
FLASK_SECRET_KEY = "FLASK_SECRET_KEY"
# REDISTOGO_URL = ""
# redis_url = REDISTOGO_URL
# redis_client = redis.from_url(redis_url, decode_responses=True)
TOKEN = ""

app = flask.Flask(__name__)
app.debug = True
app.secret_key = FLASK_SECRET_KEY


def get_dbx_app_secret(secret_id: str) -> str:
    resp = secretsmanager.get_secret_value(SecretId=secret_id)
    data = json.loads(resp["SecretString"])
    return data["dropbox_app_secret"]


def get_url(route) -> str:
    """Generate a proper URL, forcing HTTPS if not running locally"""
    host = urllib.parse.urlparse(flask.request.url).hostname
    return flask.url_for(
        route,
        _external=True,
        _scheme="http" if host in ("127.0.0.1", "localhost") else "https",
    )


def get_flow():
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    return dropbox.DropboxOAuth2Flow(
        APP_KEY,
        dbx_app_secret,
        get_url("oauth_callback"),
        flask.session,
        "dropbox-csrf-token",
    )


@app.route("/welcome")
def welcome():
    return flask.render_template(
        "welcome.html",
        redirect_url=get_url("oauth_callback"),
        webhook_url=get_url("webhook"),
        home_url=get_url("index"),
        app_key=APP_KEY,
    )


@app.route("/oauth_callback")
def oauth_callback():
    """Callback function for when the user returns from OAuth."""
    auth_result = get_flow().finish(flask.request.args)
    account = auth_result.account_id
    # Extract and store the access token for this user
    access_token = auth_result.access_token
    TOKEN = access_token
    # redis_client.hset("tokens", account, access_token)
    process_user(account)
    return flask.redirect(flask.url_for("done"))


def process_user(account):
    """Call /files/list_folder for the given user ID and process any changes."""

    # OAuth token for the user
    # token = redis_client.hget("tokens", account)
    token = TOKEN

    # cursor for the user (None the first time)
    # cursor = redis_client.hget("cursors", account)

    dbx = dropbox.Dropbox(token)
    has_more = True

    while has_more:
        if cursor is None:
            result = dbx.files_list_folder(path="")
        else:
            result = dbx.files_list_folder_continue(cursor)

        for entry in result.entries:
            # Ignore deleted files, folders, and non-markdown files
            if (
                isinstance(entry, dropbox.files.DeletedMetadata)
                or isinstance(entry, dropbox.files.FolderMetadata)
                or not entry.path_lower.endswith(".md")
            ):
                continue

            # Convert to Markdown and store as <basename>.html
            _, resp = dbx.files_download(entry.path_lower)
            html = markdown(resp.content.decode("utf-8"))
            dbx.files_upload(
                bytes(html, encoding="utf-8"),
                entry.path_lower[:-3] + ".html",
                mode=dropbox.files.WriteMode("overwrite"),
            )

        # Update cursor
        cursor = result.cursor
        # redis_client.hset("cursors", account, cursor)

        # Repeat only if there's more to do
        has_more = result.has_more


@app.route("/")
def index() -> str:
    logger.info("Index REST api endpoint was called.")
    return flask.render_template("index.html")


@app.route("/login")
def login():
    return flask.redirect(get_flow().start())


@app.route("/done")
def done() -> str:
    logger.info("Done REST api endpoint was called.")
    return flask.render_template("done.html")


@app.route("/webhook", methods=["GET"])
def challenge() -> flask.Response:
    """Respond to the webhook challenge (GET request) by echoing back the challenge parameter."""
    resp = flask.Response(flask.request.args.get("challenge"))
    resp.headers["Content-Type"] = "text/plain"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@app.route("/webhook", methods=["POST"])
def webhook() -> t.Union[t.NoReturn | str]:
    """Receive a list of changed user IDs from Dropbox and process each."""
    # Make sure this is a valid request from Dropbox
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    signature = flask.request.headers.get("X-Dropbox-Signature")
    key = bytes(dbx_app_secret, encoding="ascii")
    computed_signature = hmac.new(key, flask.request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed_signature):
        flask.abort(403)

    for account in json.loads(flask.request.data)["list_folder"]["accounts"]:
        # We need to respond quickly to the webhook request, so we do the
        # actual work in a separate thread. For more robustness, it's a
        # good idea to add the work to a reliable queue and process the queue
        # in a worker process.
        # threading.Thread(target=process_user, args=(account,)).start()
        logger.info("Process a webhook's request by a worker.")
    return ""


def lambda_handler(event, context):
    logger.info("Lambda handler was called.")
    return aws_lambda_wsgi.response(app, event, context)


if __name__ == "__main__":
    app.run()
