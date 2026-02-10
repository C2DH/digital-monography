import flask
import flask_login
import flask_wtf
import importlib
import os
import sqlmodel
import types

from src._common.constants import IS_DEBUG
from src._common.models import User

try:
    from db import db_engine
except (ImportError, ModuleNotFoundError):
    from .db import db_engine


SERVICE_NAME = "dashboard"
BLUEPRINT_MODULES: list[str] = [
    "admin.routes",
    "home.routes",
]


def _import_blueprint(module_path: str) -> types.ModuleType:
    try:
        return importlib.import_module(module_path)
    except (ModuleNotFoundError, ImportError):
        return importlib.import_module(f"src.{SERVICE_NAME}.{module_path}")


def create_app():
    """Defined in app.py so that both main.py and tests can import it."""
    app = flask.Flask(__name__, template_folder="./_templates")
    login_manager = flask_login.LoginManager()
    app.debug = IS_DEBUG
    app.secret_key = os.environ["FLASK_SECRET_KEY"]
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"

    @login_manager.user_loader
    def load_user(user_id) -> User | None:
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        with sqlmodel.Session(db_engine) as session:
            stmt = sqlmodel.select(User).where(User.id == uid)
            return session.exec(stmt).first()

    with app.app_context():
        for module_path in BLUEPRINT_MODULES:
            # import within context to avoid circular imports
            mod = _import_blueprint(module_path)
            package = module_path.split(".")[0]
            blueprint_name = f"{package}_bp"
            try:
                bp = getattr(mod, blueprint_name)
            except AttributeError as e:
                raise AttributeError(
                    f"Module '{module_path}' should have a blueprint named '{blueprint_name}'."
                )
            app.register_blueprint(bp)
    csrf = flask_wtf.CSRFProtect(app)
    return app
