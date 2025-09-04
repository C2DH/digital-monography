import alembic
import alembic.config
import flask
import logging
import os
import pathlib

from src._common.constants import DEFAULT_SFS_DIR
from src._common.constants import db_path as DB_PATH


admin_bp = flask.Blueprint("admin", __name__)


@admin_bp.route("/api/admin/hi", methods=["GET"])
@admin_bp.route("/api/admin/hi/", methods=["GET"])
def admin_hi() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    resp = flask.Response(
        response=flask.json.dumps({"site": "hi", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/api/admin/migrate", methods=["GET"])
@admin_bp.route("/api/admin/migrate/", methods=["GET"])
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


@admin_bp.route("/api/admin/unlink", methods=["DELETE"])
@admin_bp.route("/api/admin/unlink/", methods=["DELETE"])
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


@admin_bp.route("/api/admin/download-db", methods=["GET"])
@admin_bp.route("/api/admin/download-db/", methods=["GET"])
def download_db() -> flask.Response:
    """
    TODO: maybe for uploading a file ingest it from S3 using boto3's download_fileobj
    """
    # slug = flask.request.args.get("slug", "None")
    fp = pathlib.Path(DB_PATH)
    logging.info(f"File exists: {fp.exists()}")
    logging.info(f"File size: {fp.stat().st_size if fp.exists() else 'N/A'}")
    logging.info(f"File path: {fp.resolve()}")
    logging.info(f"File name: {fp.name}")
    # data = b""
    # with open(DB_PATH, "rb") as f:
    #     data = f.read()
    # resp = flask.Response(
    #     response=flask.json.dumps({}),
    #     status=200,
    #     mimetype="application/json",
    # )
    # resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    # resp.headers["Access-Control-Allow-Origin"] = "*"
    # resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return flask.send_file(fp, as_attachment=True, download_name=fp.name)
