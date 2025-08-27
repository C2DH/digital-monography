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
        from src.entrypoint.admin.routes import admin_bp
        from src.entrypoint.assets.routes import assets_bp
        from src.entrypoint.citations.routes import citations_bp
        from src.entrypoint.cloud.routes import cloud_bp
        from src.entrypoint.dropbox.routes import dropbox_bp
        from src.entrypoint.headings.routes import headings_bp

        app.register_blueprint(admin_bp)
        app.register_blueprint(assets_bp)
        app.register_blueprint(cloud_bp)
        app.register_blueprint(citations_bp)
        app.register_blueprint(dropbox_bp)
        app.register_blueprint(headings_bp)
    return app
