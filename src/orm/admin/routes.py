import alembic
import alembic.config
import flask
import logging
import os
import pathlib

from src._common.constants import DEFAULT_SFS_DIR


admin_bp = flask.Blueprint("admin", __name__)


@admin_bp.route("/hi", methods=["GET"])
@admin_bp.route("/hi/", methods=["GET"])
def hi() -> flask.Response:
    # slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "hi"}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/admin/hi", methods=["GET"])
@admin_bp.route("/admin/hi/", methods=["GET"])
def admin_hi() -> flask.Response:
    # slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "hi"}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/admin/migrate", methods=["GET"])
@admin_bp.route("/admin/migrate/", methods=["GET"])
def admin_migrate() -> flask.Response:
    """
    Migrate the database schema.
    """
    msg = {"status": "success", "message": "ok"}
    status = 200
    try:
        alembicArgs = [
            "-c",
            os.path.join("src", "_common", "alembic.ini"),
            # "--sqlalchemy-url",
            # DB_URL,
            "--raiseerr",
            "upgrade",
            "head",
        ]
        alembic.config.main(argv=alembicArgs)
    except Exception as e:
        status = 503
        logging.error(f"Error migrating database: {e}")
        msg = {"status": "error", "message": str(e)}
    resp = flask.Response(
        response=flask.json.dumps(msg, default=str),
        status=status,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/admin/unlink", methods=["DELETE"])
@admin_bp.route("/admin/unlink/", methods=["DELETE"])
def unlink() -> flask.Response:
    """
    Delete the database. This is mean only for debugging.
    TODO: Disable when the db schema stabilizes.
    """
    msg = {"status": "success", "message": "ok"}
    status = 200
    try:
        db_path = os.environ.get("DB_PATH")
        if db_path:
            db = pathlib.Path(db_path)
        else:
            db = pathlib.Path(DEFAULT_SFS_DIR) / "_database.db"
        db.unlink(missing_ok=True)
    except Exception as e:
        status = 503
        logging.error(f"Error deleting the database: {e}")
        msg = {"status": "error", "message": str(e)}
    resp = flask.Response(
        response=flask.json.dumps(msg, default=str),
        status=status,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp
