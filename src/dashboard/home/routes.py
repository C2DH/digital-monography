import flask
import pathlib
import werkzeug
import werkzeug.utils

# import flask_login
# import sqlmodel
# from src._common.models import Book

from src._common.constants import DEFAULT_SFS_DIR

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import login_required


home_bp = flask.Blueprint("home", __name__)
# home_bp.template_folder = home_bp.root_path + "/templates"


SLUG = "migration-and-HERitage"
HTML_BUILD_DIR = pathlib.Path(DEFAULT_SFS_DIR) / "_JB" / SLUG / "_build" / "html"


@home_bp.route("/", methods=["GET"])
def index() -> flask.Response:
    return flask.render_template("home/index.html")


# # def migration_and_heritage() -> flask.Response:
# @home_bp.route("/b/migration-and-heritage", methods=["GET"])
# @login_required
# def read_book() -> flask.Response:
#     iframe_src = flask.url_for("home.serve_static_site", site_path="index.html")
#     return flask.render_template(
#         "home/read.html",
#         iframe_src=iframe_src,
#     )


@home_bp.route("/b/<slug>/read/", defaults={"site_path": "index.html"}, methods=["GET"])
@home_bp.route("/b/<slug>/read/<path:site_path>", methods=["GET"])
@login_required
def serve_static_site(slug: str, site_path: str) -> flask.Response:
    """
    Serve static files from the HTML_BUILD_DIR directory, which contains the built HTML site.
    This allows us to serve the jupyter book inside the dashboard to logged-in users.

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
        prefix = flask.url_for("home.serve_static_site", site_path="", slug=slug)
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


# @admin_bp.route("/api/admin/create_user", methods=["POST"])
# @login_required
# @admin_required
# def create_user():
#     username = flask.request.args.get("username")
#     password = flask.request.args.get("password")
#     role = flask.request.args.get("role")
#     if not username or not password or not role:
#         return flask.jsonify({"error": "Missing parameters"}), 400
#     if role == UserRole.Admin:
#         return flask.jsonify({"error": "Cannot create another admin user"}), 403
#     if role not in UserRole.Editor | UserRole.Author:
#         return (
#             flask.jsonify({"error": "Invalid role"}),
#             400,
#         )
#     new_user = User(username=username, role=role)
#     new_user.set_password(password)
#     with sqlmodel.Session(db_engine) as session:
#         stmt = sqlmodel.select(User).where(User.username == username)
#         user = session.exec(stmt).first()
#         if user:
#             return flask.jsonify({"error": "User already exists"}), 400
#         session.add(new_user)
#         session.commit()
#     return flask.jsonify({"message": f"User {username} created with role {role}."}), 201


# @admin_bp.route("/api/admin/hi", methods=["GET"])
# @admin_bp.route("/api/admin/hi/", methods=["GET"])
# def admin_hi() -> flask.Response:
#     slug = flask.request.args.get("slug", "None")


# @admin_bp.route("/login", methods=["GET", "POST"])
# def login():
#     if flask.request.method == "POST":
#         # TODO: add login logic
#         if authenticated:
#             flask.session["logged_in"] = True
#             flask.session["username"] = username
#             next_url = flask.request.args.get("next") or "/"
#             return flask.redirect(next_url)
#         return flask.render_template("login.html", error="Invalid credentials")
#     return flask.render_template("login.html")


# @admin_bp.route("/logout")
# def logout():
#     flask.session.clear()
#     return flask.redirect(flask.url_for("admin.login"))
