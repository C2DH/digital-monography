import flask
import random
import typing as t

from src._common.constants import ASSETS_DIR, DEFAULT_SFS_DIR, INPUT_DIR
from src._common.keys import KeyPath

try:
    # in microservices, db and fetchers are part of the root dir
    from decorators import login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..decorators import login_required


build_bp = flask.Blueprint("build", __name__)


class TPreBuildCheckResult(t.TypedDict):
    is_manuscript_accessible: bool
    is_config_found: bool
    is_chapter_found: bool
    is_assets_dir_found: bool
    chapters: list[str]


@build_bp.route("/b/<slug>/build", methods=["GET"])
@login_required
def build_book(slug: str) -> flask.Response:
    """
    Build a Jupyter Book as a static site.
    """
    input_dir = KeyPath(DEFAULT_SFS_DIR) / INPUT_DIR / slug
    res: TPreBuildCheckResult = {
        "is_manuscript_accessible": False,
        "is_config_found": False,
        "is_chapter_found": False,
        "is_assets_dir_found": False,
        "chapters": [],
    }
    if not input_dir.exists() or not input_dir.is_dir():
        return flask.render_template("build/index.html", result=res)
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() in {".docx", ".ipynb"}:
            res["chapters"].append(path.name)
        elif path.is_file() and path.name.lower() in {"myst.yml", "myst.yaml"}:
            res["is_config_found"] = True
        elif path.is_dir() and path.name == ASSETS_DIR:
            res["is_assets_dir_found"] = True
    res["is_chapter_found"] = any(res["chapters"])
    res["is_manuscript_accessible"] = True
    return flask.render_template("build/index.html", result=res)


def verify_config(slug: str) -> bool:
    input_dir = KeyPath(DEFAULT_SFS_DIR) / INPUT_DIR / slug
    config_path = None
    for path in input_dir.iterdir():
        if path.is_file() and path.name.lower() in {"myst.yml", "myst.yaml"}:
            config_path = path
            break
    if config_path is None:
        return False
    # TODO: add actual YAML parsing and validation here
    return random.choice([True, False])
