import base64
import sys
import io
import urllib
import urllib.parse


def convert_str(s):
    """Convert bytes to str, if required"""
    print("10> type(s)", type(s))
    try:
        return s.decode("utf-8")
    except UnicodeDecodeError:
        return s


def response(app, event, context):
    print("18> type(app)", type(app))
    print("19> type(event)", type(event))
    print("20> type(context)", type(context))
    sr = StartResponse()
    output = app(environ(event, context), sr)
    print("23> type(output)", type(output))
    return sr.response(output)


class StartResponse:
    def __init__(self):
        self.status = 500
        self.headers = []
        self.body = io.StringIO()

    def __call__(self, status, headers, exc_info=None):
        print("34> type(status)", type(status))
        print("35> type(headers)", type(headers))
        print("36> type(exc_info)", type(exc_info))
        self.status = status.split()[0]
        self.headers[:] = headers
        # return self.body.write
        res = self.body.write
        print("41> type(res)", type(res))
        return res

    def response(self, output):
        print("45> type(output)", type(output))
        headers: dict[str, str] = dict(self.headers)
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
        res = {
            "statusCode": str(self.status),
            "headers": headers,
            "body": body,
            "isBase64Encoded": is_base64,
        }
        print("63> type(res)", type(res))
        return res


def environ(event, context):
    body = b""
    str_body = event.get("body")
    if str_body:
        body = bytes(str_body, "utf-8")
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
    if headers:
        for k, v in headers.items():
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

    return environ


# import typing as t
# class ResponseType(t.TypedDict):
#     statusCode: str
#     headers: dict[str, str]
#     body: str
#     isBase64Encoded: bool
