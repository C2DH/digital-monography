import bs4
import sqlmodel

from src._common.constants import (
    DEFAULT_SFS_DIR,
    CHAPTERS_DIR,
    DB_URL,
)
from src._common.keys import KeyPath
from src._common.state import DocumentState
from src._common.models import (
    Book,
)

_CHAPTERS_DIR = KeyPath(DEFAULT_SFS_DIR) / CHAPTERS_DIR
db_engine = sqlmodel.create_engine(DB_URL)


MULTI_DOCS_SLUG = "a_book"
SPLIT_DOC_SLUG = "split-to-multiple-chapters"


class TestDbRowsAfterPreparer_MultipleDocsExample:
    key_a = _CHAPTERS_DIR / MULTI_DOCS_SLUG / "01_a.html"
    key_b = _CHAPTERS_DIR / MULTI_DOCS_SLUG / "02_b.html"
    key_cr = _CHAPTERS_DIR / MULTI_DOCS_SLUG / "05_conditional_rendering.html"

    @classmethod
    def setup_class(cls):
        cls.html: dict[KeyPath, bs4.BeautifulSoup] = {}
        cls.docstates: dict[str, DocumentState] = {}
        for key in [cls.key_a, cls.key_b, cls.key_cr]:
            assert key.exists(), f"Expected {key} to exist but it does not."

    def test_authors_and_books_properly_registered(self):
        with sqlmodel.Session(db_engine) as session:
            stmt = sqlmodel.select(Book).where(Book.slug == MULTI_DOCS_SLUG)
            results = session.exec(stmt)
            books = results.all()
            _ = books[0].authors if books else []  #
        assert len(books) == 1, "There should be exactly one book with the given slug."
        assert books[0].title == "Examples of book contents"
        assert len(books[0].authors) == 1, "Book should have one author."
        assert books[0].authors[0].name == "Pawel Kaminski"
        assert books[0].authors[0].orcid == None


class TestDbRowsAfterPreparer_SplitDocExample:
    key_idx = _CHAPTERS_DIR / SPLIT_DOC_SLUG / "00_index.html"
    key_inf = _CHAPTERS_DIR / SPLIT_DOC_SLUG / "01_infile.html"
    key_uni = (
        _CHAPTERS_DIR / SPLIT_DOC_SLUG / "02_is_unicode_with_custom_file_name.html"
    )

    @classmethod
    def setup_class(cls):
        cls.html: dict[KeyPath, bs4.BeautifulSoup] = {}
        cls.docstates: dict[str, DocumentState] = {}
        for key in [cls.key_idx, cls.key_inf, cls.key_uni]:
            assert key.exists(), f"Expected {key} to exist but it does not."

    def test_authors_and_books_properly_registered(self):
        with sqlmodel.Session(db_engine) as session:
            stmt = sqlmodel.select(Book).where(Book.slug == SPLIT_DOC_SLUG)
            results = session.exec(stmt)
            books = results.all()
            _ = books[0].authors if books else []

        assert len(books) == 1, "There should be exactly one book with the given slug."
        assert books[0].title == "Split Document Example"
        assert len(books[0].authors) == 2, "Book should have two authors."
        pak = next(a for a in books[0].authors if a.name == "Pawel Kaminski")
        eli = next(a for a in books[0].authors if a.name == "Elisabeth Guerard")
        assert pak.name == "Pawel Kaminski"
        assert pak.orcid == "0009-0000-0000-0000"
        assert eli.name == "Elisabeth Guerard"
        assert eli.orcid == "0000-0001-7742-4141"
