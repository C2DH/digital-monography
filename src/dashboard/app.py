import flask
import importlib
import os
import types

from src._common.constants import IS_DEBUG


SERVICE_NAME = "dashboard"
BLUEPRINT_MODULES: list[str] = [
    "admin.routes",
    # "assets.routes",
    # "cloud.routes",
    # "citations.routes",
    # "headings.routes",
]


def _import_blueprint(module_path: str) -> types.ModuleType:
    try:
        return importlib.import_module(module_path)
    except (ModuleNotFoundError, ImportError):
        return importlib.import_module(f"src.{SERVICE_NAME}.{module_path}")


def create_app():
    """Defined in app.py so that both main.py and tests can import it."""
    app = flask.Flask(__name__)
    app.debug = IS_DEBUG
    app.secret_key = os.environ["FLASK_SECRET_KEY"]
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
    return app
