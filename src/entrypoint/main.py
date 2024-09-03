import aws_lambda_wsgi
import base64
import boto3
import binascii
import datetime
import dropbox
import fastapi
import fastapi.templating
import flask  # TODO: consider replacing flask with something microVM specific (fastapi? bottle?)
import hashlib
import hmac
import json
import os
import logging
import markdown
import pathlib
import time
import typing as t
import urllib
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


try:
    from constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
        DYNAMODB_TOKENS_TBL,
        DYNAMODB_CURSORS_TBL,
    )
except (ImportError, ModuleNotFoundError):
    from .constants import (
        IS_DEBUG,
        DROPBOX_SECRET_ID,
        DYNAMODB_TOKENS_TBL,
        DYNAMODB_CURSORS_TBL,
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


dynamodb = boto3.resource("dynamodb")
secretsmanager = boto3.client("secretsmanager")
sqs = boto3.client("sqs")


APP_KEY = "9d9sdu2khx0lboj"
FLASK_SECRET_KEY = "FLASK_SECRET_KEY"
AWS_AGW_STAGE = "test"
# TOKEN = ""

app = flask.Flask(__name__)
app.debug = True
app.secret_key = FLASK_SECRET_KEY
# app.wsgi_app = werkzeug.middleware.dispatcher.DispatcherMiddleware(
# app.wsgi_app = dispatcher.DispatcherMiddleware(
#     werkzeug.exceptions.NotFound(), {"/test": app.wsgi_app}
# )
# app.config["SERVER_NAME"] = "20cks5gkc3.execute-api.eu-west-1.amazonaws.com"
# app.config["APPLICATION_ROOT"] = "/test"
# app.config["PREFERRED_URL_SCHEME"] = "https"

fapp = fastapi.FastAPI()
fapp.add_middleware(SessionMiddleware, secret_key=FLASK_SECRET_KEY)
templates = fastapi.templating.Jinja2Templates(directory="templates")


class UserData(t.TypedDict):
    users: list[int]

class AccountsData(t.TypedDict):
    accounts: list[str]


class FlaskRequestData(t.TypedDict):
    # {'delta': {'users': [635421248]}, 'list_folder': {'accounts': ['dbid:AAC4AZN7bGg-92mRl_JqfdGDY8vV-d0xwpk']}}
    delta: UserData
    list_folder: UserData


def get_dbx_app_secret(secret_id: str) -> str:
    resp = secretsmanager.get_secret_value(SecretId=secret_id)
    data = json.loads(resp["SecretString"])
    return data["dropbox_app_secret"]


def get_url(route) -> str:
    """Generate a proper URL, forcing HTTPS if not running locally."""
    # host = urllib.parse.urlparse(flask.request.url).hostname
    host = urllib.parse.urlparse(flask.request.url).hostname
    # print("host", host)
    # print("route", route)
    # print("flask.request.url", flask.request.url)
    # print(
    #     "urllib.parse.urlparse(flask.request.url)",
    #     urllib.parse.urlparse(flask.request.url),
    # )
    is_local = host in ("127.0.0.1", "localhost")
    url = flask.url_for(
        route,
        _external=True,
        _scheme="http" if is_local else "https",
        # _scheme="http" if host in ("127.0.0.1", "localhost") else "https",
    )
    # solution 1
    start = time.perf_counter()
    url_parts = urllib.parse.urlparse(url)
    url_parts = url_parts._replace(path=f"/{AWS_AGW_STAGE}" + url_parts.path)
    res1 = urllib.parse.urlunparse(url_parts)
    logger.info("Res1 == " + res1 + str(time.perf_counter() - start))
    # solution 2
    start = time.perf_counter()
    schema_end = 7 if is_local else 8
    netloc_end = url[schema_end:].index("/")
    res2 = (
        url[: schema_end + netloc_end]
        + f"/{AWS_AGW_STAGE}/"
        + url[schema_end + netloc_end + 1 :]
    )
    logger.info("Res2 == " + res2 + str(time.perf_counter() - start))
    return res1

    # "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com/welcome"
    # "http://127.0.0.1:5000/welcome"
    # return url


def get_flow(session=None):
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    if session:
        logger.info("FastAPI session == " + json.dumps(session, default=str))
    if flask.session:
        logger.info("Flask.session == " + json.dumps(flask.session, default=str))
        logger.info("Flask.session == " + json.dumps(flask.session, default=str))
        try:
            logger.info(
                "Flask.session == " + json.dumps(flask.session.items(), default=str)
            )
        except Exception as e:
            pass
    return dropbox.DropboxOAuth2Flow(
        consumer_key=APP_KEY,
        consumer_secret=dbx_app_secret,
        redirect_uri=get_url("oauth_callback"),
        session=flask.session if session is None else session,
        csrf_token_session_key="dropbox-auth-csrf-token",
        # token_access_type="offline", # I don't see such argument
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
    logger.info(
        "oauth_callback path received the following args:"
        + json.dumps(
            flask.request.args.to_dict(),
            default=str,
        )
    )
    logger.info("args==" + json.dumps(args, default=str))
    logger.info("kwargs==" + json.dumps(kwargs, default=str))
    auth_result = get_flow().finish(flask.request.args)
    logger.info("auth_result: " + str(auth_result))
    account = auth_result.account_id
    logger.info("account: " + str(account))
    # Extract and store the access token for this user
    access_token = auth_result.access_token
    logger.info("access_token: " + str(access_token))
    # TOKEN = access_token
    # redis_client.hset("tokens", account, access_token)
    logger.info('Here was: `redis_client.hset("tokens", account, access_token)`')
    dynamodb_set(
        DYNAMODB_TOKENS_TBL, **{"account": account, "access_token": access_token}
    )
    process_user(account)
    return flask.redirect(get_url("done"))
    # return flask.redirect(flask.url_for("done"))


def process_user(account):
    """Call /files/list_folder for the given user ID and process any changes."""
    logger.info("process_user function was invoked with account " + str(account))
    # OAuth token for the user
    # token = redis_client.hget("tokens", account)
    logger.info('Here was: `token = redis_client.hget("tokens", account)`')
    tokens_resp = dynamodb_get(DYNAMODB_TOKENS_TBL, {"account": account})
    logger.info("tokens_resp == " + json.dumps(tokens_resp, default=str))
    token = tokens_resp.get("Item", {}).get("access_token")
    logger.info(f"token == {token}")
    # token = TOKEN

    # cursor for the user (None the first time)
    # cursor = redis_client.hget("cursors", account)
    logger.info('Here was: `redis_client.hget("cursors", account)`')
    cursors_resp = dynamodb_get(DYNAMODB_CURSORS_TBL, {"account": account})
    cursor = cursors_resp.get("Item", {}).get("cursor")

    dbx = dropbox.Dropbox(token)
    has_more = True

    while has_more:
        if cursor is None:
            result = dbx.files_list_folder(path="")
        else:
            result = dbx.files_list_folder_continue(cursor)

        for entry in result.entries:
            logger.info("dir(entry)" + json.dumps(dir(entry), default=str))
            logger.info(f"entry.name {entry.name}")
            logger.info(f"entry.path_lower {entry.path_lower}")

            # Ignore deleted files, folders, and non-markdown files
            if (
                isinstance(entry, dropbox.files.DeletedMetadata)
                or isinstance(entry, dropbox.files.FolderMetadata)
                or not entry.path_lower.endswith(".md")
            ):
                continue

            # Convert to Markdown and store as <basename>.html
            _, resp = dbx.files_download(entry.path_lower)
            html = markdown.markdown(resp.content.decode("utf-8"))
            logger.info("html == " + html)
            dbx.files_upload(
                bytes(html, encoding="utf-8"),
                entry.path_lower[:-3] + ".html",
                mode=dropbox.files.WriteMode("overwrite"),
            )
            logger.info(f"New file '{entry.path_lower[:-3] + '.html'}' was uploaded.")

        # Update cursor
        cursor = result.cursor
        # redis_client.hset("cursors", account, cursor)
        logger.info('Here was: `redis_client.hset("cursors", account, cursor)`')
        dynamodb_set(DYNAMODB_CURSORS_TBL, **{"account": account, "cursor": cursor})

        # Repeat only if there's more to do
        has_more = result.has_more
        logger.info('result.has_more loop in process_user has ended.')
    logger.info('process_user has ended.')


def generate_csrf(server_secret, session_secret, form_id, time, salt):
    # <form action='/' method='POST' autocomplete="off">
    # <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    # </form>
    time = time.strftime("%Y.%m.%d.%H.%M")
    if type(form_id) is str:
        form_id = form_id.encode("utf-8")
    hasher = hashlib.sha256
    msg = hasher(
        b"|".join((salt, server_secret, session_secret, form_id, time.encode("ascii")))
    ).digest()
    return "|".join(
        (
            "v1",
            time,
            binascii.hexlify(salt).decode("ascii"),
            binascii.hexlify(msg).decode("ascii"),
        )
    )


@app.route("/")
def index() -> str:
    logger.info("Index REST api endpoint was called.")
    return flask.render_template("index.html", **{"csrf_token": ""})


@app.route("/login")
def login(*args, **kwargs):
    logger.info("Login REST api endpoint was called.")
    flow = get_flow()
    logger.info("Login REST api flow == " + json.dumps(flow, default=str))
    authorize_url = flow.start()
    logger.info("Login REST api authorize_url == " + json.dumps(flow, default=str))
    return flask.redirect(authorize_url)


@fapp.get("/index", response_class=fastapi.responses.HTMLResponse)
def index2(request: Request) -> str:
    logger.info("Index2 REST api endpoint was called.")
    logger.info("Index2 REST api request ==" + json.dumps(request, default=str))
    if request:
        logger.info("Index REST api request session == " + request.session)
    return templates.TemplateResponse(request=request, name="item.html")
    # return flask.render_template("index.html")


@fapp.get("/login2")
def login2(request: Request):
    logger.info("Login2 REST api endpoint was called.")
    logger.info("Login2 REST api request ==" + json.dumps(request, default=str))
    if request:
        logger.info("Login REST api request session == " + request.session)
    authorize_url = get_flow(request.session).start()
    logger.info("Login REST api generated authorize_url : " + str(authorize_url))
    return RedirectResponse(authorize_url)


# @fapp.get("/login")
# def login():
#     logger.info("Login REST api endpoint was called.")
#     return flask.redirect(get_flow().start())


@app.route("/done")
def done() -> str:
    logger.info("Done REST api endpoint was called.")
    return flask.render_template("done.html")


@app.route("/webhook", methods=["GET"])
def challenge() -> flask.Response:
    """Respond to the webhook challenge (GET request) by echoing back the challenge parameter."""
    logger.info("Webhook REST api endpoint was called with GET (challenge).")
    logger.info(
        "webhook path received the following args:"
        + json.dumps(
            flask.request.args.to_dict(),
            default=str,
        )
    )
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
    # Make sure this is a valid request from Dropbox
    logger.info("Webhook REST api endpoint was called with POST.")
    logger.info(
        "webhook path received the following args:"
        + json.dumps(
            flask.request.args.to_dict(),
            default=str,
        )
    )
    logger.info(
        "webhook path received the following json:"
        + json.dumps(
            flask.request.json,
            default=str,
        )
    )
    logger.info(
        "webhook path received the following data:"
        + json.dumps(
            json.loads(flask.request.data),
            default=str,
        )
    )
    dbx_app_secret = get_dbx_app_secret(DROPBOX_SECRET_ID)
    signature = flask.request.headers.get("X-Dropbox-Signature")
    key = bytes(dbx_app_secret, encoding="ascii")
    computed_signature = hmac.new(key, flask.request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed_signature):
        logger.info("Digests from signature and computed_signature are not equal. " +
                    "Exiting with 'Forbidden' status code.")
        flask.abort(403)

    _send_msg_to_sqs(flask.request.data)


    # for account in json.loads(flask.request.data)["list_folder"]["accounts"]:
        # We need to respond quickly to the webhook request, so we do the
        # actual work in a separate thread. For more robustness, it's a
        # good idea to add the work to a reliable queue and process the queue
        # in a worker process.
        # process_user(account)
        # logger.info("Passing a process request to a separate thread.")
        # threading.Thread(target=process_user, args=(account,)).start()
        # logger.info("Process a webhook's request by a worker.")
    return ""


def _send_msg_to_sqs(request_data: FlaskRequestData) -> None:
    logger.info(f"Preparing to send a message to the sqs queue.")
    logger.info("Os.environ: " + json.dumps(os.environ, default=str))
    try:
        QueueUrl = os.environ["SQS_URL"]
        MessageBody = base64.b64encode(json.dumps(request_data, default=str))
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
    logger.info(f"{json.dumps({"expire_at": expire_at, **kwargs}, default=str)}")
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
    logger.info("Lambda handler was called.")
    logger.info("Event == " + json.dumps(event, default=str))
    logger.info("Context == " + json.dumps(context, default=str))
    logger.info("Event cookies" + event.get("headers", {}).get("Cookie", ""))
    return aws_lambda_wsgi.response(app, event, context)


# with app.app_context():
#     logger.info(
#         "oauth_callback"
#         + flask.url_for("oauth_callback", _external=True, _scheme="https")
#     )
#     logger.info("oauth_callback" + flask.url_for("oauth_callback", _scheme="https"))
#     logger.info("webhook" + flask.url_for("webhook", _external=True, _scheme="https"))
#     logger.info("webhook" + flask.url_for("webhook", _scheme="https"))
#     logger.info("index" + flask.url_for("index", _external=True, _scheme="https"))
#     logger.info("index" + flask.url_for("index", _scheme="https"))


if __name__ == "__main__":
    IS_DEBUG = True
    app.run()
