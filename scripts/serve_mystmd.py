import argparse
import http.server
import pathlib
import socketserver
import typing as t


PORT = 8003
DIRECTORY = "/tmp/efs/a_book/_build/html"
parser = argparse.ArgumentParser(description="...")
parser.add_argument("book_path")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


@t.runtime_checkable
class has_book_path(t.Protocol):
    book_path: str


if __name__ == "__main__":
    args = parser.parse_args()
    if isinstance(args, has_book_path):
        assert isinstance(args.book_path, str)
        book_path_arg = args.book_path.split("=")
        book_path = pathlib.Path(book_path_arg[1]) / "_build" / "html"
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()
