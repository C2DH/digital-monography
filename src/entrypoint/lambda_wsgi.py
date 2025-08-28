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
    print("10> type(s)", type(s))
    try:
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return s
    except UnicodeDecodeError:
        return s


def response(
    app: flask.app.Flask, event: APIGatewayProxyEventV2, context: LambdaContext
):
    print("18> type(app)", type(app))
    print("19> type(event)", type(event))
    print("20> type(context)", type(context))
    sr = StartResponse()
    output = app(environ(event, context), sr)
    print(
        "isinstance(output, werkzeug.wsgi.ClosingIterator)",
        isinstance(output, werkzeug.wsgi.ClosingIterator),
    )
    # assert isinstance(output, werkzeug.wsgi.ClosingIterator)
    print("23> type(output)", type(output))
    return sr.response(output)


class StartResponse:
    def __init__(self):
        self.status: int | str = 500
        self.headers = []
        self.body = io.StringIO()

    def __call__(
        self, status, headers: list, exc_info: t.Any | None = None
    ) -> t.Callable:
        print("34> type(status)", type(status), status)
        print("35> type(headers)", type(headers))
        for h in headers:
            print("35> type(header)", type(h), h)
        print("36> type(exc_info)", type(exc_info))
        assert isinstance(status, str)
        self.status = status.split()[0]
        print("54> type(self.status)", type(self.status), self.status)
        self.headers[:] = headers
        # return self.body.write
        res = self.body.write
        print("41> type(res)", type(res))
        return res

    def response(self, output: werkzeug.wsgi.ClosingIterator):
        print("45> type(output)", type(output))
        headers: dict[str, str] = dict(self.headers)
        body: str | bytes
        if headers.get("Content-Type") in [
            "image/png",
            "image/gif",
            "application/octet-stream",
        ]:
            is_base64 = True
            body = base64.b64encode(b"".join(output)).decode("ascii")
            print("52> type(body)", type(body))
        else:
            is_base64 = False
            body = self.body.getvalue() + "".join(map(convert_str, output))
            print("53> type(body)", type(body))
        res = {
            "statusCode": str(self.status),
            "headers": headers,
            "body": body,
            "isBase64Encoded": is_base64,
        }
        print("63> type(res)", type(res))
        return res


def environ(event: APIGatewayProxyEventV2, _: LambdaContext) -> dict[str, t.Any]:
    str_body = event.get("body", "")
    print("89> type(str_body)", type(str_body), str_body)
    body = bytes(str_body, "utf-8") if str_body else b""
    environ = {
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
    headers = event.get("headers", {})
    assert isinstance(headers, dict)
    if headers:
        print("105> headers")
        for k, v in headers.items():
            print("type(k)", type(k), k)
            print("type(v)", type(v), v)
            # assert isinstance(k, str)
            # assert isinstance(v, str)
            k = k.upper().replace("-", "_")
            if k == "CONTENT_TYPE":
                environ["CONTENT_TYPE"] = v
            elif k == "HOST":
                environ["SERVER_NAME"] = v
            elif k == "X_FORWARDED_FOR":
                environ["REMOTE_ADDR"] = v.split(", ")[0]
            elif k == "X_FORWARDED_PROTO":
                environ["wsgi.url_scheme"] = v
            elif k == "X_FORWARDED_PORT":
                environ["SERVER_PORT"] = v
            environ["HTTP_" + k] = v
    print("121> environ")
    for key, val in environ.items():
        print("type(key)", type(key), key)
        print("type(val)", type(val), val)
    return environ


# import typing as t
# class ResponseType(t.TypedDict):
#     statusCode: str
#     headers: dict[str, str]
#     body: str
#     isBase64Encoded: bool
