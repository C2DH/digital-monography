import subprocess

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

_tasks: dict[str, subprocess.Popen] = {}


class TPreBuildCheckResult(t.TypedDict):
    is_manuscript_accessible: bool
    is_config_found: bool
    is_chapter_found: bool
    is_assets_dir_found: bool
    chapters: list[str]


@build_bp.route("/b/<slug>/build/1/pre-check", methods=["GET"])
@login_required
def pre_check(slug: str) -> flask.Response:
    """
    Check the preconditions for preparing manuscript transformation to Jupyter Book.
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
        "is_assets_dir_found": f'The "{ASSETS_DIR}" directory could not be found. Every author\'s package should include an "{ASSETS_DIR}" folder with all figures and other media files.',
        "is_chapter_found": "No chapters were found. Make sure that the author's package includes at least one chapter file and that the chapter file was properly uploaded. We accept chapters written in .docx and .ipynb formats.",
    }
    if not input_dir.exists() or not input_dir.is_dir():
        return flask.render_template(
            "build/pre-check.html", result=res, slug=slug, msgs=msgs
        )
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower() in {".docx", ".ipynb"}:
            res["chapters"].append(path.name)
        elif path.is_file() and path.name.lower() in {"myst.yml", "myst.yaml"}:
            res["is_config_found"] = True
            msgs["is_config_found"] = (
                f'"{path.name}" was found. Configuration will be verified during the next step.'
            )
        elif path.is_dir() and path.name == ASSETS_DIR:
            res["is_assets_dir_found"] = True
            msgs["is_assets_dir_found"] = (
                f'The "{ASSETS_DIR}" directory was found. Make sure that all media files are included in this directory and properly linked in the manuscript.'
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
    return flask.render_template(
        "build/pre-check.html", result=res, slug=slug, msgs=msgs
    )


EXAMPLE_LIST = [
    {"chapter": "Chapter 1: Introduction", "status": "success"},
    {"chapter": "Chapter 2: Literature Review", "status": "success"},
    {"chapter": "Chapter 3: Methodology", "status": "failed"},
]


_WAITING_FRAGMENT = """
<div id="chapters-status"
     hx-get="{{ url_for('build.get_chapters', slug=slug) }}"
     hx-trigger="every 2s"
     hx-swap="outerHTML">
    <p class="flex items-center gap-2 text-amber-700">
        <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" opacity="0.25"></circle>
            <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
        </svg>
        Waiting for task to complete...
    </p>
</div>
"""

_RESULT_FRAGMENT = """
<div id="chapters-status">
    <ul class="space-y-2">
        {% for item in chapters %}
        <li class="flex items-center justify-between rounded-md border border-gray-200 bg-white p-3">
            <span class="text-sm font-medium text-gray-900">{{ item.chapter }}</span>
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                {{ 'bg-emerald-100 text-emerald-700' if item.status == 'success' else 'bg-rose-100 text-rose-700' }}">
                {{ item.status }}
            </span>
        </li>
        {% endfor %}
    </ul>
</div>
"""


@build_bp.route("/b/<slug>/build/2/chapters", methods=["GET"])
@login_required
def trigger_build(slug: str) -> flask.Response:
    """
    Start a background sleep task and return the chapters page.
    HTMX polls /list-of-chapters until the task completes, then shows EXAMPLE_LIST.
    """
    _tasks[slug] = subprocess.Popen(["sleep", "5"])
    print("_tasks", _tasks)
    return flask.render_template("build/chapters.html", slug=slug)


@build_bp.route("/b/<slug>/build/2/list-of-chapters", methods=["GET"])
@login_required
def get_chapters(slug: str) -> flask.Response:
    proc = _tasks.get(slug)
    print("proc", proc)
    print("proc.poll()", proc.poll())  # if proc.poll() == 0, process completed
    if proc is None or proc.poll() is None:
        return flask.render_template_string(_WAITING_FRAGMENT, slug=slug)
    return flask.render_template_string(_RESULT_FRAGMENT, chapters=EXAMPLE_LIST)
