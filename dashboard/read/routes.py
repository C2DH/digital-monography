import flask
import pathlib
import werkzeug
import werkzeug.utils

from src._common.constants import DEFAULT_SFS_DIR


try:
    # in microservices, db and fetchers are part of the root dir
    from decorators import login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..decorators import login_required


read_bp = flask.Blueprint("read", __name__)


# TODO: move to separate blueprint for books or /read endpoint
@read_bp.route("/b/<slug>/read/", defaults={"site_path": "index.html"}, methods=["GET"])
@read_bp.route("/b/<slug>/read/<path:site_path>", methods=["GET"])
@login_required
def serve_static_site(slug: str, site_path: str) -> flask.Response:
    """
    Serve static files from the `_JB/<slug>/_build/html` directory,
    which contains the built HTML site. This allows us to serve the
    jupyter book inside the dashboard to logged-in users.

    @param site_path: The path to the requested file within the site.
    Root is the _build/html directory. For example, for
    "/_JB/some-slug/_build/html/myst-theme.css" site_path is "myst-theme.css".
    Path converter (<path:site_path>) allows slashes in the variable part,
    so we can have nested paths like "subdir/file.html". See:
    https://flask.palletsprojects.com/en/stable/quickstart/#variable-rules
    """
    built_dir = pathlib.Path(DEFAULT_SFS_DIR) / "_JB" / slug / "_build" / "html"
    safe_path = werkzeug.utils.safe_join(str(built_dir), site_path)
    if safe_path is None:
        flask.abort(404)
    requested_path = pathlib.Path(safe_path)
    if requested_path.is_dir():
        requested_path = requested_path / "index.html"
    if not requested_path.exists():
        flask.abort(404)  # TODO: maybe go to list of available books?
    if not requested_path.is_file():
        flask.abort(404)  # TODO: maybe go to list of available books?

    if requested_path.suffix.lower() == ".html":
        html = requested_path.read_text(encoding="utf-8")
        prefix = flask.url_for("read.serve_static_site", site_path="", slug=slug)
        if not prefix.endswith("/"):
            prefix = f"{prefix}/"
        html = html.replace(' href="/', f' href="{prefix}')
        html = html.replace(" href='/", f" href='{prefix}")
        html = html.replace(' src="/', f' src="{prefix}')
        html = html.replace(" src='/", f" src='{prefix}")
        html = html.replace(' content="/', f' content="{prefix}')
        html = html.replace(" content='/", f" content='{prefix}")
        html = html.replace('url("/', f'url("{prefix}')
        html = html.replace("url('/", f"url('{prefix}")
        return flask.Response(html, mimetype="text/html")
    else:
        relative_file = requested_path.relative_to(built_dir)
        assert str(relative_file) == site_path  # TODO: remove after few examples
        # Seems to me we can skip relative_to() and just use site_path directly,
        # but let's keep it for safety
        return flask.send_from_directory(built_dir, str(relative_file))
