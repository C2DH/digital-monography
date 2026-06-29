import flask
import flask_login
import flask_wtf
import sqlmodel
import wtforms

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


class LoginForm(flask_wtf.FlaskForm):
    username = wtforms.StringField(
        "Username", validators=[wtforms.validators.DataRequired()]
    )
    password = wtforms.PasswordField(
        "Password", validators=[wtforms.validators.DataRequired()]
    )


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        next_url = flask.request.args.get("next") or "/"
        if not username or not password:
            return flask.render_template(
                "admin/login.html", error="Missing username or password", form=form
            )
        print("flask.request.host", flask.request.host)
        # TODO: check if next_url is safe to redirect to (i.e. same host)
        # to prevent open redirect vulnerabilities
        # if not url_has_allowed_host_and_scheme(next, request.host):
        #     return flask.abort(400)
        with sqlmodel.Session(db_engine) as session:
            stmt = sqlmodel.select(User).where(User.username == username)
            user = session.exec(stmt).first()
            if user and user.check_password(password):
                flask_login.login_user(user)
                return flask.redirect(next_url)
        return flask.render_template(
            "admin/login.html", error="Invalid credentials", form=form
        )
    return flask.render_template("admin/login.html", form=form)


@flask_login.login_required
@admin_bp.route("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("admin.login"))
