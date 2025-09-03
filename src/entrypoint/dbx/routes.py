import dropbox  # type: ignore[import-untyped]
import flask
import hashlib
import hmac
import json
import logging
import os
import typing as t
import urllib
import urllib.parse

from .aws import dynamodb_set, secretsmanager, send_msg_to_sqs


dbx_bp = flask.Blueprint("dbx", __name__, template_folder="templates")


@dbx_bp.route("/", methods=["GET"])
def index() -> str:
    logging.info("Index REST api endpoint was called.")
    infra_env = os.environ.get("INFRA_ENV")
    return flask.render_template(
        "index.html", data={"login_path": f"/{infra_env}/login"}
    )


@dbx_bp.route("/welcome", methods=["GET"])
@dbx_bp.route("/welcome/", methods=["GET"])
def welcome():
    logging.info("Welcome REST api endpoint was called.")
    return flask.render_template(
        "welcome.html",
        redirect_url=get_url("dbx.oauth_callback"),
        webhook_url=get_url("dbx.webhook"),
        home_url=get_url("dbx.index"),
        app_key=os.environ["DROPBOX_APP_KEY"],
    )


@dbx_bp.route("/oauth_callback", methods=["GET"])
@dbx_bp.route("/oauth_callback/", methods=["GET"])
def oauth_callback(*args, **kwargs):
    """Callback function for when the user returns from OAuth."""
    logging.info("oauth_callback REST api endpoint was called.")
    print("oauth_callback REST api endpoint was called.")
    logging.info(json.dumps(flask.request.args, default=str))
    print(json.dumps(flask.request.args, default=str))
    auth_result = get_flow().finish(flask.request.args)
    logging.info("auth_result get_flow().finish(flask.request.args)")
    print("auth_result get_flow().finish(flask.request.args)")
    account = auth_result.account_id
    logging.info(f"Account ID: {account}")
    print(f"Account ID: {account}")
    # Extract and store the access token for this user
    access_token = auth_result.access_token
    logging.info(f"Access Token: {access_token}")
    print(f"Access Token: {access_token}")
    table = os.environ.get("DYNAMODB_TOKENS_TBL", "")
    logging.info(f"Tokens Table: {table}")
    print(f"Tokens Table: {table}")
    dynamodb_set(table, **{"account": account, "access_token": access_token})
    logging.info(f'get_url("dbx.done")={get_url("dbx.done")}')
    print(f'get_url("dbx.done")={get_url("dbx.done")}')
    return flask.redirect(get_url("dbx.done"))


@dbx_bp.route("/login", methods=["GET"])
@dbx_bp.route("/login/", methods=["GET"])
def login(*args, **kwargs):
    logging.info("Login REST api endpoint was called.")
    authorize_url = get_flow().start()
    logging.info(f"Authorize URL: {authorize_url}")
    print(f"Authorize URL: {authorize_url}")
    return flask.redirect(authorize_url)


@dbx_bp.route("/done", methods=["GET"])
@dbx_bp.route("/done/", methods=["GET"])
def done() -> str:
    logging.info("Done REST api endpoint was called.")
    # url = "https://cpy-dgtmon-dev-staticws-dashboard.s3.eu-west-1.amazonaws.com/index.html"
    dashboard_url = "https://" + os.environ["DASHBOARD_DOMAIN"] + "/index.html"
    dbx_app_dir = os.environ["DROPBOX_APP_DIR"]
    dbx_app_url = f"https://www.dropbox.com/home/Apps/{dbx_app_dir}"
    return flask.render_template(
        "done.html",
        data={
            "dashboard_url": dashboard_url,
            "dbx_app_url": dbx_app_url,
            "env": os.environ.get("INFRA_ENV", ""),
        },
    )


@dbx_bp.route("/webhook", methods=["GET"])
@dbx_bp.route("/webhook/", methods=["GET"])
def challenge() -> flask.Response:
    """Respond to the webhook challenge (GET request) by echoing back the challenge parameter."""
    logging.info("Webhook REST api endpoint was called with GET (challenge).")
    resp = flask.Response(flask.request.args.get("challenge"))
    resp.headers["Content-Type"] = "text/plain"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@dbx_bp.route("/webhook", methods=["POST"])
@dbx_bp.route("/webhook/", methods=["POST"])
def webhook() -> t.Union[t.NoReturn | str]:
    """
    Handle POST webhook requests by sending messages to an SQS queue.
    Important: the Entrypoint AWS Lambda has only 10 seconds to respond to
    a webhook request! Thus, the only action it takes is to send messages to
    the SQS queue. The messages are received by the Dropbox AWS Lambda,
    which will call the Dropbox API `/files/list_folder/` or
    `/files/list_folder/continue` endpoint and upload files to AWS S3.
    """
    logging.info("Webhook REST api endpoint was called with POST.")
    # Make sure this is a valid request from Dropbox
    secret_id = os.environ.get("DROPBOX_SECRET_ID", "")
    dbx_app_secret = get_dbx_app_secret(secret_id)
    signature = flask.request.headers.get("X-Dropbox-Signature", "")
    key = bytes(dbx_app_secret, encoding="ascii")
    computed_signature = hmac.new(key, flask.request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed_signature):
        logging.info(
            "Digests from signature and computed_signature are not equal. "
            + "Exiting with 'Forbidden' status code."
        )
        flask.abort(403)
    send_msg_to_sqs(flask.request.data)
    return ""


def get_dbx_app_secret(secret_id: str) -> str:
    resp = secretsmanager.get_secret_value(SecretId=secret_id)
    data = json.loads(resp["SecretString"])
    return data["dropbox_app_secret"]


def get_url(route) -> str:
    """Generate a proper URL, forcing HTTPS if not running locally."""
    host = urllib.parse.urlparse(flask.request.url).hostname
    is_local = host in ("127.0.0.1", "localhost")
    url = flask.url_for(
        route,
        _external=True,
        _scheme="http" if is_local else "https",
    )
    # Include the stage part of the url, e.g https://.../test/...
    url_parts = urllib.parse.urlparse(url)
    agw_stage = os.environ.get("INFRA_ENV")
    # url_parts = url_parts._replace(path=f"/{AWS_AGW_STAGE}" + url_parts.path)
    url_parts = url_parts._replace(path=f"/{agw_stage}" + url_parts.path)
    return urllib.parse.urlunparse(url_parts)


def get_flow() -> dropbox.DropboxOAuth2Flow:
    """
    Returns DropboxOAuth2Flow object, which has 2 important methods:
    * start()
        Builds an authorization URL, where a user will be
        automatically redirected to enter his/hers Dropbox credentials.
        It also saves CSRF token.
    * finish()
        After a user has visited the authorization URL and logged in,
        dropbox will check CSRF token and, if access was not denied,
        fetch an access token. Returns `dropbox.OAuth2FlowResult`.
    """
    secret_id = os.environ.get("DROPBOX_SECRET_ID", "")
    dbx_app_secret = get_dbx_app_secret(secret_id)
    logging.info("len(dbx_app_secret)", len(dbx_app_secret))
    print("len(dbx_app_secret)", len(dbx_app_secret))
    logging.info(f'get_url("dbx.oauth_callback")={get_url("dbx.oauth_callback")}')
    print(f'get_url("dbx.oauth_callback")={get_url("dbx.oauth_callback")}')
    logging.info(f"flask.session={flask.session}")
    print(f"flask.session={flask.session}")
    return dropbox.DropboxOAuth2Flow(
        consumer_key=os.environ["DROPBOX_APP_KEY"],
        consumer_secret=dbx_app_secret,
        redirect_uri=get_url("dbx.oauth_callback"),
        session=flask.session,
        csrf_token_session_key="dropbox-auth-csrf-token",
    )
