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
            from admin.routes import admin_bp
            from assets.routes import assets_bp
            from citations.routes import citations_bp
            from cloud.routes import cloud_bp
            from headings.routes import headings_bp
        except (ModuleNotFoundError, ImportError):
            # in local testing, the modules is present in src.<microservice> dir
            from src.orm.admin.routes import admin_bp
            from src.orm.assets.routes import assets_bp
            from src.orm.citations.routes import citations_bp
            from src.orm.cloud.routes import cloud_bp
            from src.orm.headings.routes import headings_bp

        app.register_blueprint(admin_bp)
        app.register_blueprint(assets_bp)
        app.register_blueprint(cloud_bp)
        app.register_blueprint(citations_bp)
        app.register_blueprint(headings_bp)
    return app
