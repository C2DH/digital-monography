import flask
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
        "is_assets_dir_found": False,
        "is_config_found": False,
        "is_chapter_found": False,
        "chapters": [],
    }
    msgs = {
        "is_manuscript_accessible": "The manuscript directory is could not be found. Check if you uploaded author's package correctly.",
        "is_config_found": '"myst.yml" could not be found. Make sure that the author\'s package includes a valid "myst.yml" file in the root of the manuscript directory.',
        "is_assets_dir_found": f'The "{ASSETS_DIR}/" directory could not be found. Every author\'s package should include an "{ASSETS_DIR}/" folder with all figures and other media files.',
        "is_chapter_found": "No chapters were found. Make sure that the author's package includes at least one chapter file and that the chapter file was properly uploaded. We accept chapters written in .docx and .ipynb formats.",
    }
    if not input_dir.exists() or not input_dir.is_dir():
        return flask.render_template(
            "build/index.html", result=res, slug=slug, msgs=msgs
        )
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() in {".docx", ".ipynb"}:
            res["chapters"].append(path.name)
        elif path.is_file() and path.name.lower() in {"myst.yml", "myst.yaml"}:
            res["is_config_found"] = True
            msgs["is_config_found"] = (
                f"`{path.name}` was found. Configuration will be verified during the next step."
            )
        elif path.is_dir() and path.name == ASSETS_DIR:
            res["is_assets_dir_found"] = True
            msgs["is_assets_dir_found"] = (
                f'The "{ASSETS_DIR}/" directory was found. Make sure that all media files are included in this directory and properly linked in the manuscript.'
            )
    res["is_chapter_found"] = any(res["chapters"])
    if res["is_chapter_found"]:
        msgs["is_chapter_found"] = (
            "The program was able to locate the following manuscript files: "
            + ", ".join(res["chapters"])
            + "."
        )
    res["is_manuscript_accessible"] = True
    msgs["is_manuscript_accessible"] = (
        "The manuscript directory is present and accessible."
    )
    return flask.render_template("build/index.html", result=res, slug=slug, msgs=msgs)
