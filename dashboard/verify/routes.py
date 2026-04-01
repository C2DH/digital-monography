import flask
import random
import time
import typing as t

from src._common.constants import DEFAULT_SFS_DIR, INPUT_DIR
from src._common.keys import KeyPath

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


verify_bp = flask.Blueprint("verify", __name__)


@verify_bp.route("/b/<slug>/verify/", methods=["GET"])
def index() -> flask.Response:
    return (
        flask.jsonify({"todo": "display verify results"}),
        200,
    )


class TVerifyConfigResult(t.TypedDict):
    is_config_valid: bool
    msg: str


@verify_bp.route("/b/<slug>/verify/config", methods=["GET"])
@login_required
def verify_config(slug: str) -> flask.Response:
    is_config_valid, msg = mock_verif_cfg(slug)
    time.sleep(random.uniform(0.5, 2.0))  # simulate processing time
    if flask.request.headers.get("HX-Request") == "true":
        return (
            flask.render_template(
                "verify/_config_validity_check.html",
                is_config_valid=is_config_valid,
                message=msg,
            ),
            200,
        )
    return flask.jsonify({"is_config_valid": is_config_valid, "message": msg}), 200


def mock_verif_cfg(slug: str) -> tuple[bool, str]:
    input_dir = KeyPath(DEFAULT_SFS_DIR) / INPUT_DIR / slug
    config_path = None
    for path in input_dir.iterdir():
        if path.is_file() and path.name.lower() in {"myst.yml", "myst.yaml"}:
            config_path = path
            break
    if config_path is None:
        msg = f"Config file not found in {input_dir}"
        return False, msg
    # TODO: add YAML verification
    msg = f"Random result."
    return random.choice([True, False]), msg
