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


@home_bp.route("/migration-and-heritage", methods=["GET"])
@login_required
def migration_and_heritage() -> flask.Response:
    iframe_src = flask.url_for(
        "home.migration_and_heritage_site", site_path="index.html"
    )
    return flask.render_template(
        "home/migration_and_heritage.html",
        iframe_src=iframe_src,
    )


@home_bp.route(
    "/migration-and-heritage/site/",
    defaults={"site_path": "index.html"},
    methods=["GET"],
)
@home_bp.route("/migration-and-heritage/site/<path:site_path>", methods=["GET"])
@login_required
def migration_and_heritage_site(site_path: str) -> flask.Response:
    print("\n", "=" * 25)
    print("HTML_BUILD_DIR", HTML_BUILD_DIR)
    print("site_path", site_path)
    safe_path = werkzeug.utils.safe_join(str(HTML_BUILD_DIR), site_path)
    if safe_path is None:
        flask.abort(404)
    requested_path = pathlib.Path(safe_path)
    print("requested_path", requested_path)
    if requested_path.is_dir():
        requested_path = requested_path / "index.html"
    if not requested_path.exists():
        flask.abort(404)
    if not requested_path.is_file():
        flask.abort(404)

    if requested_path.suffix.lower() == ".html":
        html = requested_path.read_text(encoding="utf-8")
        print("html", html[:2000])
        prefix = flask.url_for("home.migration_and_heritage_site", site_path="")
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
        relative_file = requested_path.relative_to(HTML_BUILD_DIR)
        print("relative_file", relative_file)
        return flask.send_from_directory(HTML_BUILD_DIR, str(relative_file))


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
