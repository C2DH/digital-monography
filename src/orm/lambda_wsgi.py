from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
import base64
import flask
import io
import sys
import typing as t
import urllib
import urllib.parse
import werkzeug
import werkzeug.wsgi


def convert_str(s: bytes | str):
    """Convert bytes to str, if required"""
    try:
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return s
    except UnicodeDecodeError:
        return s


def response(
    app: flask.app.Flask, event: APIGatewayProxyEventV2, context: LambdaContext
):
    sr = StartResponse()
    output = app(environ(event, context), sr)
    assert isinstance(output, werkzeug.wsgi.ClosingIterator)
    return sr.response(output)


class StartResponse:
    def __init__(self):
        self.status: int | str = 500
        self.headers = []
        self.body = io.StringIO()

    def __call__(
        self, status: t.Any, headers: list, exc_info: t.Any | None = None
    ) -> t.Callable:
        assert isinstance(status, str)
        self.status = status.split()[0]
        self.headers[:] = headers
        return self.body.write

    def response(self, output: werkzeug.wsgi.ClosingIterator):
        headers: dict[str, str] = dict(self.headers)
        body: str | bytes
        if headers.get("Content-Type") in [
            "image/png",
            "image/gif",
            "application/octet-stream",
        ]:
            is_base64 = True
            body = base64.b64encode(b"".join(output)).decode("ascii")
        else:
            is_base64 = False
            body = self.body.getvalue() + "".join(map(convert_str, output))
        return {
            "statusCode": str(self.status),
            "headers": headers,
            "body": body,
            "isBase64Encoded": is_base64,
        }


def environ(event: APIGatewayProxyEventV2, _: LambdaContext) -> dict[str, t.Any]:
    str_body = event.get("body", "")
    body = bytes(str_body, "utf-8") if str_body else b""
    environ: dict[str, t.Any] = {
        "REQUEST_METHOD": event["httpMethod"],
        "SCRIPT_NAME": "",
        "PATH_INFO": event["path"],
        "QUERY_STRING": urllib.parse.urlencode(event["queryStringParameters"] or {}),
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_LENGTH": str(len(body) or ""),
        "HTTP": "on",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    headers: dict[str, t.Any] | None = event.get("headers", {})
    if headers:
        for k, v in headers.items():
            k = k.upper().replace("-", "_")
            if k == "CONTENT_TYPE":
                environ["CONTENT_TYPE"] = v
            elif k == "HOST":
                environ["SERVER_NAME"] = v
            elif k == "X_FORWARDED_FOR":
                assert isinstance(v, str)
                environ["REMOTE_ADDR"] = v.split(", ")[0]
            elif k == "X_FORWARDED_PROTO":
                environ["wsgi.url_scheme"] = v
            elif k == "X_FORWARDED_PORT":
                environ["SERVER_PORT"] = v
            environ["HTTP_" + k] = v
    return environ
