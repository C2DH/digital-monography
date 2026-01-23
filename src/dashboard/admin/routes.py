import flask
import flask_login
import sqlmodel

from src._common.models import User
from src._common.constants import UserRole

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


admin_bp = flask.Blueprint("admin", __name__)


@admin_bp.route("/api/admin/create_user", methods=["POST"])
@login_required
@admin_required
def create_user():
    username = flask.request.args.get("username")
    password = flask.request.args.get("password")
    role = flask.request.args.get("role")
    if not username or not password or not role:
        return flask.jsonify({"error": "Missing parameters"}), 400
    if role == UserRole.Admin:
        return flask.jsonify({"error": "Cannot create another admin user"}), 403
    if role not in UserRole.Editor | UserRole.Author:
        return (
            flask.jsonify({"error": "Invalid role"}),
            400,
        )
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.select(User).where(User.username == username)
        user = session.exec(stmt).first()
        if user:
            return flask.jsonify({"error": "User already exists"}), 400
        session.add(new_user)
        session.commit()
    return flask.jsonify({"message": f"User {username} created with role {role}."}), 201


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
