import functools
import flask
import flask_login
from flask_login.mixins import AnonymousUserMixin

from src._common.constants import UserRole
from src._common.models import User


# TODO: decorator to check if user is author of THE resource


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if isinstance(flask_login.current_user, AnonymousUserMixin):
            return flask.render_template("home/401_unauthorized.html"), 401
        assert isinstance(flask_login.current_user, User)
        if flask_login.current_user.is_authenticated:
            return f(*args, **kwargs)
        return flask.render_template("home/401_unauthorized.html"), 401

    return decorated_function


def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if isinstance(flask_login.current_user, AnonymousUserMixin):
            return flask.render_template("home/401_unauthorized.html"), 401
        assert isinstance(flask_login.current_user, User)
        if (
            flask_login.current_user.is_authenticated
            and flask_login.current_user.has_role(UserRole.Admin)
        ):
            return f(*args, **kwargs)
        return flask.render_template("home/403_forbidden.html"), 403

    return decorated_function


def editor_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if isinstance(flask_login.current_user, AnonymousUserMixin):
            return flask.render_template("home/401_unauthorized.html"), 401
        assert isinstance(flask_login.current_user, User)
        if (
            flask_login.current_user.is_authenticated
            and flask_login.current_user.has_role(UserRole.Editor)
        ):
            return f(*args, **kwargs)
        return flask.render_template("home/403_forbidden.html"), 403

    return decorated_function
