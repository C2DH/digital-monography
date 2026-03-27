import flask
import flask_login
import sqlmodel
from sqlalchemy.orm import selectinload
import random
import time

from src._common.constants import DEFAULT_SFS_DIR, JB_DIR
from src._common.models import Book
from src._common.keys import KeyPath

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


home_bp = flask.Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def book_index() -> flask.Response:
    """
    Displays a list of books and their authors.
    """
    if not flask_login.current_user.is_authenticated:
        return flask.render_template("home/index.html", books=[])
    jb_dir = KeyPath(DEFAULT_SFS_DIR) / JB_DIR
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.select(Book).options(selectinload(Book.authors))
        books = session.exec(stmt).all()

    books_json: list[dict] = []
    for book in books:
        book_data = book.model_dump(mode="json")
        book_data["authors"] = [
            author.model_dump(mode="json") for author in book.authors
        ]
        books_json.append(book_data)
    return flask.render_template("home/index.html", books=books_json)


@home_bp.route("/b/<slug>/process", methods=["GET"])
@login_required
def process_book(slug: str) -> flask.Response:
    """
    Simulates an async task that fetches additional data for a book.
    """
    wait_time = random.uniform(0.5, 3.0)
    time.sleep(wait_time)
    # with sqlmodel.Session(db_engine) as session:
    #     book = session.get(Book, book_id)
    #     if not book:
    #         return flask.Response("Book not found", status=404)
    return flask.Response(f"Processed in {wait_time:.2f}s")


@home_bp.route("/b/<slug>/home/static_site", methods=["GET"])
def get_jb_link(slug: str) -> flask.Response:
    built_jb_dir = KeyPath(DEFAULT_SFS_DIR) / JB_DIR / slug / "_build" / "html"
    if built_jb_dir.exists():
        url = flask.url_for("read.serve_static_site", slug=slug)
        return f'<a href="{url}" target="_blank" class="text-indigo-600 hover:text-indigo-800 underline">▶️</a>'
    return "❌"
