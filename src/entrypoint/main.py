# import aws_lambda_wsgi
import base64
import boto3
import datetime
import dropbox  # type: ignore[import-untyped]
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import hashlib
import hmac
import json
import os
import logging
import pathlib
import typing as t
import urllib
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import (
    event_source,
    APIGatewayProxyEventV2,
)


try:
    from constants import (
        IS_DEBUG,
        APKG_UPLOAD_BUCKET_NAME,
        DROPBOX_SECRET_ID,
        DYNAMODB_AUDIT_TBL,
        DYNAMODB_ALERTS_TBL,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_REFS_TBL,
        DYNAMODB_TOKENS_TBL,
        VERIFIER_MSGS,
    )
    from lambda_wsgi import response as lambda_wsgi_response
except (ImportError, ModuleNotFoundError):
    from .constants import (  # type: ignore
        IS_DEBUG,
        APKG_UPLOAD_BUCKET_NAME,
        DROPBOX_SECRET_ID,
        DYNAMODB_AUDIT_TBL,
        DYNAMODB_ALERTS_TBL,
        DYNAMODB_ASSETS_TBL,
        DYNAMODB_CITATIONS_TBL,
        DYNAMODB_HEADINGS_TBL,
        DYNAMODB_REFS_TBL,
        DYNAMODB_TOKENS_TBL,
        VERIFIER_MSGS,
    )
    from .lambda_wsgi import response as lambda_wsgi_response  # type: ignore

from mypy_boto3_dynamodb.client import DynamoDBClient as boto3_DynamoDBClient
from mypy_boto3_dynamodb.type_defs import (
    GetItemOutputTypeDef as boto3_GetItemOutputTypeDef,
)
from mypy_boto3_s3.client import S3Client as boto3_S3Client
from mypy_boto3_s3.type_defs import ObjectTypeDef as boto3_ObjectTypeDef
from mypy_boto3_sqs import SQSClient as boto3_SQSClient

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


dynamodb: boto3_DynamoDBClient = boto3.resource("dynamodb")
secretsmanager = boto3.client("secretsmanager")
sqs: boto3_SQSClient = boto3.client("sqs")
s3: boto3_S3Client = boto3.client("s3")


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
    secret_id = os.environ.get("DROPBOX_SECRET_ID", "")
    dbx_app_secret = get_dbx_app_secret(secret_id)
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
    table = os.environ.get("DYNAMODB_TOKENS_TBL", "")
    dynamodb_set(table, **{"account": account, "access_token": access_token})
    return flask.redirect(get_url("done"))


@app.route("/")
def index() -> str:
    logger.info("Index REST api endpoint was called.")
    return flask.render_template("index.html")


def _s3_list_objects(bucket: str, prefix: t.Optional[str]) -> list[boto3_ObjectTypeDef]:
    if prefix:
        # objects = s3.list_objects_v2(Bucket=bucket, Prefix=f"{slug}/")
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
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
    contents = _s3_list_objects(os.environ.get("VERIFIER_MSGS", ""), f"{slug}/")
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
def list_assets_from_s3() -> flask.Response:
    """List objects in a upload slug/assets/* bucket."""
    logger.info("List assets REST api endpoint was called with GET.")
    slug = flask.request.args.get("slug")
    bucket = os.environ.get("APKG_UPLOAD_BUCKET_NAME", "")
    contents = _s3_list_objects(bucket, prefix=f"{slug}/assets/")
    resp = flask.Response(
        response=flask.json.dumps(contents),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@app.route("/assets", methods=["GET"])
def list_assets_from_dynamodb() -> flask.Response:
    """Retrieve assets from the database and return them to the client."""
    logger.info("Retrieve assets from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb.query(
        TableName=os.environ.get("DYNAMODB_ASSETS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
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


@app.route("/refs", methods=["GET"])
def list_refs_from_dynamodb() -> flask.Response:
    """Retrieve refs from the database and return them to the client."""
    logger.info("Retrieve refs from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb.query(
        TableName=os.environ.get("DYNAMODB_REFS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
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


@app.route("/events", methods=["GET"])
def query_events() -> flask.Response:
    """Retrieve events from the database and return them to the client."""
    logger.info("Retrieve events from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb.query(
        TableName=os.environ.get("DYNAMODB_AUDIT_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
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


@app.route("/alerts", methods=["GET"])
def query_alerts() -> flask.Response:
    """Retrieve alerts from the database and return them to the client."""
    logger.info("Retrieve alerts from the database and return them to the client.")
    resp = dynamodb.scan(
        TableName=os.environ.get("DYNAMODB_ALERTS_TBL", ""),
    )
    contents = resp["Items"]
    logger.info(f"Resp: {json.dumps(resp, default=str)}")
    while "LastEvaluatedKey" in resp:
        resp = dynamodb.scan(
            TableName=os.environ.get("DYNAMODB_ALERTS_TBL", ""),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        logger.info(f"Resp: {json.dumps(resp, default=str)}")
        contents.extend(resp["Items"])
    logger.info(f"Contents: {json.dumps(contents, default=str)}")
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
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb.query(
        TableName=os.environ.get("DYNAMODB_CITATIONS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
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


@app.route("/headings", methods=["GET"])
def query_headings() -> flask.Response:
    """Retrieve headings from the database and return them to the client."""
    logger.info("Retrieve headings from the database and return them to the client.")
    slug = flask.request.args.get("slug")
    assert slug is not None, "Error: slug was not provided"
    contents = dynamodb.query(
        TableName=os.environ.get("DYNAMODB_HEADINGS_TBL", ""),
        KeyConditionExpression="slug = :slug",
        ExpressionAttributeValues={":slug": {"S": slug}},
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
    url = "https://cpy-dgtmon-dev-staticws-dashboard.s3.eu-west-1.amazonaws.com/index.html"
    return flask.render_template("done.html", data={"url": url})


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
    secret_id = os.environ.get("DROPBOX_SECRET_ID", "")
    dbx_app_secret = get_dbx_app_secret(secret_id)
    signature = flask.request.headers.get("X-Dropbox-Signature", "")
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


def _send_msg_to_sqs(request_data: bytes) -> None:
    try:
        QueueUrl = os.environ.get("SQS_URL", "")
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
    dyndb = boto3.resource("dynamodb")
    table = dyndb.Table(tbl)
    resp = table.put_item(Item={"expire_at": expire_at, **kwargs})
    logger.info(
        f"Response from dynamodb.Table({tbl}).put_item: {json.dumps(resp, default=str)}"
    )
    # resp = dyndb.put_item(TableName=tbl, Item={"expire_at": {"N": expire_at}, **kwargs})
    # logger.info(
    #     f"Response from dynamodb.put_item(TableName={tbl}): {json.dumps(resp, default=str)}"
    # )


def dynamodb_get(tbl: str, pk: dict[str, str]) -> boto3_GetItemOutputTypeDef:
    # table = dynamodb.Table(tbl)
    # resp = table.get_item(Key=pk)
    resp = dynamodb.get_item(TableName=tbl, Key=pk)
    logger.info(
        f"Response from dynamodb.get_item(TableName={tbl}): {json.dumps(resp, default=str)}"
    )
    return resp


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context: LambdaContext):
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Context: {json.dumps(context, default=str)}")
    return lambda_wsgi_response(app, event, context)
