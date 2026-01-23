import functools
import flask
import flask_login

from src._common.constants import UserRole

# TODO: current use type
# TODO: decorator to check if user is author of THE resource


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if flask_login.current_user.is_authenticated:
            return f(*args, **kwargs)
        flask.abort(401)  # Unauthorized

    return decorated_function


def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            flask_login.current_user.is_authenticated
            and flask_login.current_user.has_role(UserRole.Admin)
        ):
            return f(*args, **kwargs)
        flask.abort(403)  # Forbidden

    return decorated_function


def editor_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            flask_login.current_user.is_authenticated
            and flask_login.current_user.has_role(UserRole.Editor)
        ):
            return f(*args, **kwargs)
        flask.abort(403)  # Forbidden

    return decorated_function
