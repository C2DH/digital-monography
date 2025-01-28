import aws_lambda_wsgi
import base64
import boto3
import datetime
import dropbox
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import hashlib
import hmac
import json
import os
import logging
import pathlib
import typing as t
import urllib


try:
    from constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
        DYNAMODB_AUDIT_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_TOKENS_TBL,
        METADATA_ASSETS_BUCKET_NAME,
        VERIFIER_MSGS,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
        DYNAMODB_AUDIT_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_TOKENS_TBL,
        METADATA_ASSETS_BUCKET_NAME,
        VERIFIER_MSGS,
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


dynamodb = boto3.client("dynamodb")
secretsmanager = boto3.client("secretsmanager")
sqs = boto3.client("sqs")
s3 = boto3.client("s3")


APP_KEY = "9d9sdu2khx0lboj"
FLASK_SECRET_KEY = "FLASK_SECRET_KEY"
AWS_AGW_STAGE = "test"

app = flask.Flask(__name__)
app.debug = True
app.secret_key = FLASK_SECRET_KEY


class UserData(t.TypedDict):
    users: list[int]


class AccountsData(t.TypedDict):
    accounts: list[str]


class FlaskRequestData(t.TypedDict):
    """Example of the request data:
    {'delta': {'users': [635421248]},
     'list_folder': {'accounts': ['dbid:AAC4AZN7bGg-92mRl_JqfdGDY8vV-d0xwpk']}}
    """

    delta: UserData
    list_folder: UserData


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
    url_parts = url_parts._replace(path=f"/{AWS_AGW_STAGE}" + url_parts.path)
    return urllib.parse.urlunparse(url_parts)


def get_flow():
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    return dropbox.DropboxOAuth2Flow(
        consumer_key=APP_KEY,
        consumer_secret=dbx_app_secret,
        redirect_uri=get_url("oauth_callback"),
        session=flask.session,
        csrf_token_session_key="dropbox-auth-csrf-token",
    )


@app.route("/welcome")
def welcome():
    logger.info("Welcome REST api endpoint was called.")
    return flask.render_template(
        "welcome.html",
        redirect_url=get_url("oauth_callback"),
        webhook_url=get_url("webhook"),
        home_url=get_url("index"),
        app_key=APP_KEY,
    )


@app.route("/oauth_callback")
def oauth_callback(*args, **kwargs):
    """Callback function for when the user returns from OAuth."""
    logger.info("oauth_callback REST api endpoint was called.")
    auth_result = get_flow().finish(flask.request.args)
    account = auth_result.account_id
    # Extract and store the access token for this user
    access_token = auth_result.access_token
    dynamodb_set(
        DYNAMODB_TOKENS_TBL, **{"account": account, "access_token": access_token}
    )
    return flask.redirect(get_url("done"))


@app.route("/")
def index() -> str:
    logger.info("Index REST api endpoint was called.")
    return flask.render_template("index.html")


def _s3_list_objects(bucket: str, slug: t.Optional[str]):
    if slug:
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=f"{slug}/")
    else:
        objects = s3.list_objects_v2(Bucket=bucket)
    if "Contents" in objects:
        return objects["Contents"]
    else:
        return []


@app.route("/list-warnings", methods=["GET"])
def list_warnings() -> flask.Response:
    """List objects in a warnings bucket."""
    logger.info("List warnings REST api endpoint was called with GET.")
    slug = flask.request.args.get("slug")
    contents = _s3_list_objects(VERIFIER_MSGS, slug)
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/list-assets", methods=["GET"])
def list_assets() -> flask.Response:
    """List objects in the metadata assets bucket."""
    logger.info("List metadata assets REST api endpoint was called with GET.")
    slug = flask.request.args.get("slug")
    contents = _s3_list_objects(METADATA_ASSETS_BUCKET_NAME, slug)
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/events", methods=["GET"])
def query_events() -> flask.Response:
    """Retrieve events from the database and return them to the client."""
    logger.info("Retrieve events from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    contents = dynamodb.query(
        TableName=DYNAMODB_AUDIT_TBL,
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={
            ":slug": { "S": slug }
        },
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/citations", methods=["GET"])
def query_citations() -> flask.Response:
    """Retrieve citations from the database and return them to the client."""
    logger.info("Retrieve citations from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    contents = dynamodb.query(
        TableName=DYNAMODB_CITATIONS_TBL,
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={
            ":slug": { "S": slug }
        },
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/headers", methods=["GET"])
def query_headers() -> flask.Response:
    """Retrieve headers from the database and return them to the client."""
    logger.info("Retrieve headers from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    contents = dynamodb.query(
        TableName=DYNAMODB_HEADINGS_TBL,
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={
            ":slug": { "S": slug }
        },
    )
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/login")
def login(*args, **kwargs):
    logger.info("Login REST api endpoint was called.")
    authorize_url = get_flow().start()
    return flask.redirect(authorize_url)


@app.route("/done")
def done() -> str:
    logger.info("Done REST api endpoint was called.")
    return flask.render_template("done.html")


@app.route("/webhook", methods=["GET"])
def challenge() -> flask.Response:
    """Respond to the webhook challenge (GET request) by echoing back the challenge parameter."""
    logger.info("Webhook REST api endpoint was called with GET (challenge).")
    resp = flask.Response(flask.request.args.get("challenge"))
    resp.headers["Content-Type"] = "text/plain"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@app.route("/webhook", methods=["POST"])
def webhook() -> t.Union[t.NoReturn | str]:
    """
    Handle POST webhook requests by sending messages to an SQS queue.
    Important: the Entrypoint AWS Lambda has only 10 seconds to respond to
    a webhook request! Thus, the only action it takes is to send messages to
    the SQS queue. The messages are received by the Dropbox AWS Lambda,
    which will call the Dropbox API `/files/list_folder/` or
    `/files/list_folder/continue` endpoint and upload files to AWS S3.
    """
    logger.info("Webhook REST api endpoint was called with POST.")
    # Make sure this is a valid request from Dropbox
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    signature = flask.request.headers.get("X-Dropbox-Signature")
    key = bytes(dbx_app_secret, encoding="ascii")
    computed_signature = hmac.new(key, flask.request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed_signature):
        logger.info(
            "Digests from signature and computed_signature are not equal. "
            + "Exiting with 'Forbidden' status code."
        )
        flask.abort(403)
    _send_msg_to_sqs(flask.request.data)
    return ""


def _send_msg_to_sqs(request_data: FlaskRequestData) -> None:
    try:
        QueueUrl = os.environ["SQS_URL"]
        MessageBody = base64.b64encode(request_data).decode("utf-8")
        resp = sqs.send_message(
            QueueUrl=QueueUrl,
            MessageBody=MessageBody,
        )
        logger.info(
            f"Response from sqs.send_message(QueueUrl={QueueUrl}, MessageBody={MessageBody}): "
            + json.dumps(resp, default=str)
        )
    except Exception as e:
        logger.exception(f"Sending a message to sqs queue failed. Error: {repr(e)}")
        raise


def dynamodb_set(tbl: str, **kwargs) -> None:
    expire_at = int((datetime.datetime.now() + datetime.timedelta(days=3)).timestamp())
    table = dynamodb.Table(tbl)
    resp = table.put_item(Item={"expire_at": expire_at, **kwargs})
    logger.info(
        f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
    )


def dynamodb_get(tbl: str, pk: dict[str, str]) -> dict[str, t.Any]:
    table = dynamodb.Table(tbl)
    resp = table.get_item(Key=pk)
    logger.info(
        f"Response from dynamodb.Table({tbl}).get_item: {json.dumps(resp, default=str)}"
    )
    return resp


def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Context: {json.dumps(context, default=str)}")
    return aws_lambda_wsgi.response(app, event, context)
