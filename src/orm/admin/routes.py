import alembic
import alembic.command
import alembic.config
import alembic.script
import boto3
import datetime
import flask
import json
import logging
import os
import pathlib
from mypy_boto3_s3.client import S3Client as boto3_S3Client

from src._common.constants import DB_URL, DEFAULT_SFS_DIR, IS_DEBUG
from src._common.constants import db_path as DB_PATH


admin_bp = flask.Blueprint("admin", __name__)


if IS_DEBUG:
    s3 = None
else:
    s3: boto3_S3Client = boto3.client("s3")


@admin_bp.route("/api/admin/hi", methods=["GET"])
@admin_bp.route("/api/admin/hi/", methods=["GET"])
def admin_hi() -> flask.Response:
    slug = flask.request.args.get("slug", "None")
    alembic_ini = os.path.join("src", "_common", "alembic.ini")
    alembic_ini_exists = os.path.exists(alembic_ini)
    logging.info(f"alembic.ini exists: {alembic_ini_exists}")
    logging.info(f"alembic_ini: {alembic_ini}")
    resp = flask.Response(
        response=flask.json.dumps({"site": "hi", "slug": slug}),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/api/admin/db/migrate", methods=["GET"])
@admin_bp.route("/api/admin/db/migrate/", methods=["GET"])
def admin_migrate() -> flask.Response:
    """
    Migrate the database schema.
    """
    msg = {"status": "success", "message": "ok"}
    status = 200
    try:
        # alembicArgs = [
        #     "-c",
        #     os.path.join("src", "_common", "alembic.ini"),
        #     "--raiseerr",
        #     "upgrade",
        #     "head",
        # ]
        # alembic.config.main(argv=alembicArgs)

        aleini = os.path.join("src", "_common", "alembic.ini")
        cfg = alembic.config.Config(aleini)
        cfg.set_main_option("sqlalchemy.url", DB_URL)
        script = alembic.script.ScriptDirectory.from_config(cfg)
        logging.info(f"script.env_py_location={script.env_py_location}")
        logging.info(
            f"script.version_locations={json.dumps(script.version_locations, default=str)}"
        )
        logging.info(f"script.env_py_location={script.env_py_location}")
        logging.info(f"1) script.versions={script.versions}")
        logging.info(
            f"1) script.get_heads()={json.dumps(script.get_heads(), default=str)}"
        )
        logging.info(f"1) script.get_current_head()={script.get_current_head()}")
        alembic.command.upgrade(cfg, "head")
        logging.info(f"2) script.versions={script.versions}")
        logging.info(
            f"2) script.get_heads()={json.dumps(script.get_heads(), default=str)}"
        )
        logging.info(f"2) script.get_current_head()={script.get_current_head()}")
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


@admin_bp.route("/api/admin/db/unlink", methods=["DELETE"])
@admin_bp.route("/api/admin/db/unlink/", methods=["DELETE"])
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


@admin_bp.route("/api/admin/db/export", methods=["GET"])
@admin_bp.route("/api/admin/db/export/", methods=["GET"])
def export_db() -> flask.Response:
    fp = pathlib.Path(DB_PATH)
    logging.info(f"File {fp.name} exists: {fp.exists()}")
    s3_bucket = os.environ["ADMIN_DATA_BUCKET_NAME"]
    with open(fp, "rb") as fileobj:
        s3resp = s3.put_object(Body=fileobj, Bucket=s3_bucket, Key=fp.name)
        logging.info(
            f"Response from s3.put_object(Bucket={s3_bucket}, Key={fp.name}): "
            + json.dumps(s3resp, default=str)
        )
    try:
        st_atime = datetime.datetime.fromtimestamp(
            fp.stat().st_atime, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        st_mtime = datetime.datetime.fromtimestamp(
            fp.stat().st_mtime, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logging.warning(f"Error getting file times: {e}")
        st_atime = str(fp.stat().st_atime)
        st_mtime = str(fp.stat().st_mtime)
    resp = flask.Response(
        response=flask.json.dumps(
            {
                "status": "ok",
                "message": "Database uploaded to S3",
                "st_size": fp.stat().st_size,
                "st_atime": st_atime,
                "st_mtime": st_mtime,
            }
        ),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


@admin_bp.route("/api/admin/db/import", methods=["GET"])
@admin_bp.route("/api/admin/db/import/", methods=["GET"])
def import_db() -> flask.Response:
    fp = pathlib.Path(DB_PATH)
    logging.info(f"File exists: {fp.exists()}")
    logging.info(f"File size: {fp.stat().st_size if fp.exists() else 'N/A'}")
    logging.info(f"File path: {fp.resolve()}")
    logging.info(f"File name: {fp.name}")
    s3_bucket = os.environ["ADMIN_DATA_BUCKET_NAME"]
    with open(fp, "wb") as fileobj:
        s3resp = s3.download_fileobj(Bucket=s3_bucket, Key=fp.name, Fileobj=fileobj)
        logging.info(
            f"Response from s3.download_fileobj(Bucket={s3_bucket}, Key={fp.name}): "
            + json.dumps(s3resp, default=str)
        )
    try:
        st_atime = datetime.datetime.fromtimestamp(
            fp.stat().st_atime, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
        st_mtime = datetime.datetime.fromtimestamp(
            fp.stat().st_mtime, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logging.warning(f"Error getting file times: {e}")
        st_atime = str(fp.stat().st_atime)
        st_mtime = str(fp.stat().st_mtime)
    resp = flask.Response(
        response=flask.json.dumps(
            {
                "status": "ok",
                "message": "Database uploaded to EFS",
                "st_size": fp.stat().st_size,
                "st_atime": st_atime,
                "st_mtime": st_mtime,
            }
        ),
        status=200,
        mimetype="application/json",
    )
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "OPTIONS,GET"
    return resp


# import alembic.command
# def run_migrations(db_url: str = DB_URL) -> None:
#     # alembicArgs = [
#     #     "-c",
#     #     os.path.join("src", "_common", "alembic.ini"),
#     #     "--raiseerr",
#     #     "upgrade",
#     #     "head",
#     # ]
#     alini = os.path.join("src", "_common", "alembic.ini")
#     cfg = alembic.config.Config(alini)
#     cfg.set_main_option("sqlalchemy.url", db_url)
#     alembic.command.upgrade(cfg, "head")
#     # alembic.config.main(argv=alembicArgs)
