import flask
import flask_login
import sqlmodel
from sqlalchemy.orm import selectinload

from src._common.models import Book

try:
    # in microservices, db and fetchers are part of the root dir
    from db import db_engine
    from decorators import admin_required, login_required
except (ImportError, ModuleNotFoundError):
    # in local testing, db and decorators are one directory up
    from ..db import db_engine
    from ..decorators import admin_required, login_required


home_bp = flask.Blueprint("home", __name__)


@flask_login.login_required
@home_bp.route("/", methods=["GET"])
def book_index() -> flask.Response:
    """
    Displays a list of books and their authors.
    """
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
