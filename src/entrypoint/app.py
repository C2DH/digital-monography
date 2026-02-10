import flask
import os

from src._common.constants import IS_DEBUG


def create_app():
    """
    Defined in app.py so that both main.py and tests can import it.
    """
    app = flask.Flask(__name__)
    app.debug = IS_DEBUG
    app.secret_key = os.environ["FLASK_SECRET_KEY"]
    with app.app_context():
        # this is to prevent circular imports
        try:
            # in lambda, the directories are copied to the root dir
            from dbx.routes import dbx_bp
        except (ModuleNotFoundError, ImportError):
            # in local testing, the modules is present in src.<microservice> dir
            from src.entrypoint.dbx.routes import dbx_bp

        app.register_blueprint(dbx_bp)
    return app
